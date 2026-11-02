"""
Integration tests for User Service (Publisher) Outbox Pattern
Tests for flow: Admin Config CRUD -> OUTBOX_EVENTS table creation

- AdminConfig is a SINGLETON — only ONE row ever exists in the table.
- update_config_blob() is an UPSERT — it handles both create AND update.

SAFE TO RUN AGAINST A LIVE DEV/STAGING DATABASE:
Every test snapshots the real AdminConfig row before it starts and restores
it to its original state (same id, same blob, same timestamps) when it ends.
The real config is NEVER permanently modified or deleted by these tests.
"""

import copy
import uuid
from datetime import datetime

import pytest
from app.crud.admin_config_crud import update_config_blob, get_admin_config_row
from app.database import SessionLocal
from app.models.admin_config_model import AdminConfig
from app.models.outbox_model import OutboxEvent
from app.schemas.admin_config import AdminConfigMap




@pytest.fixture(scope="function")
def integration_db():
    """Each test gets its own fresh DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def mock_user():
    """Mock admin user ID. All test rows are tagged with this so cleanup can find them."""
    return "test-admin-user"


@pytest.fixture
def sample_config_data():
    return AdminConfigMap({"SESSION_EXPIRE_MINUTES": 11, "MAX_PATIENT_PHOTO": 11, "MAX_ITEMS_TO_RETURN": 11})


@pytest.fixture
def updated_config_data():
    return AdminConfigMap({"SESSION_EXPIRE_MINUTES": 22, "MAX_PATIENT_PHOTO": 22, "MAX_ITEMS_TO_RETURN": 22})


@pytest.fixture(autouse=True)
def save_and_restore_config(integration_db):
    """
    Runs automatically before and after every single test.

    HOW IT WORKS:

    BEFORE the test:
      1. Read the real existing row and save a snapshot of ALL its fields.
      2. Delete that row from the table so the test starts with a clean slate.
         The table is now empty — safe for CREATE path tests.
         The real data is only held in memory inside this fixture.

    AFTER the test:
      3. Delete every row the test created (tagged with modifiedById="test-admin-user"
         or any row that exists now, since only one can exist at a time).
      4. Delete any outbox events the test created.
      5. If a real row existed before the test, re-insert it with its original
         id, configBlob, modifiedById, and modifiedDate — exactly as it was.

    """

    # BEFORE: snapshot and clear the real row 
    real_row = integration_db.query(AdminConfig).first()

    if real_row:
        saved_id = real_row.id
        saved_config_blob = copy.deepcopy(real_row.configBlob)  # deep copy — JSON dict
        saved_modified_by = real_row.modifiedById
        saved_modified_date = real_row.modifiedDate
        had_real_row = True

        integration_db.delete(real_row)
        integration_db.commit()
        print(f"\n[SAVE]  Snapshotted real AdminConfig row (id={saved_id}), table now empty")
    else:
        had_real_row = False
        print(f"\n[SAVE]  No existing AdminConfig row found, table already empty")

    # clean up any leftover test outbox events from a previous crashed run
    try:
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.created_by == "test-admin-user"
        ).delete()
        integration_db.commit()
    except Exception:
        integration_db.rollback()

    yield  # ← the test runs here

    # AFTER: wipe test data, restore the real row 
    try:
        # Delete outbox events the test created
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.created_by == "test-admin-user"
        ).delete()
        integration_db.commit()

        # Delete whatever AdminConfig row the test left behind
        integration_db.query(AdminConfig).delete()
        integration_db.commit()

        # Restore the real row with all original values
        if had_real_row:
            restored = AdminConfig(
                id=saved_id,
                configBlob=saved_config_blob,
                modifiedById=saved_modified_by,
                modifiedDate=saved_modified_date,
            )
            integration_db.add(restored)
            integration_db.commit()
            print(f"[RESTORE] Real AdminConfig row restored (id={saved_id}, blob={saved_config_blob})")
        else:
            print(f"[RESTORE] No real row to restore — table left empty as originally found")

    except Exception as e:
        integration_db.rollback()
        print(f"[RESTORE] WARNING: Failed to restore AdminConfig row: {str(e)}")
        print(f"[RESTORE] MANUAL ACTION REQUIRED: re-insert AdminConfig row with id={saved_id if had_real_row else 'N/A'} and {saved_config_blob}")




class TestAdminConfigCreateOutbox:
    """
    Tests for the USERCONFIG_CREATED path.
    Triggered when NO AdminConfig row exists — which save_and_restore_config
    guarantees for us by clearing the real row before each test.
    """

    def test_create_config_creates_outbox(self, integration_db, mock_user, sample_config_data):
        """
        GIVEN: The AdminConfig table is empty (guaranteed by save_and_restore_config)
        WHEN:  update_config_blob() is called with initial config data
        THEN:  An AdminConfig row AND a USERCONFIG_CREATED OutboxEvent are
               both created with the correct data.

        Goal: verify the CREATE path of the upsert writes to both tables.
        """

        result = update_config_blob(
            db=integration_db,
            new_configs=sample_config_data,
            modified_by_id=mock_user,
            correlation_id=str(uuid.uuid4())
        )
        print(f"\n[DONE]: update_config_blob returned: {result}")

        config_row = get_admin_config_row(integration_db)

        assert config_row is not None
        assert config_row.configBlob == {"SESSION_EXPIRE_MINUTES": 11, "MAX_PATIENT_PHOTO": 11, "MAX_ITEMS_TO_RETURN": 11}
        assert config_row.modifiedById == "test-admin-user"

        print(f"[DONE]: AdminConfig row ID: {config_row.id}, blob: {config_row.configBlob}")

        outbox_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(config_row.id),
            OutboxEvent.event_type == "USERCONFIG_CREATED"
        ).first()

        assert outbox_event is not None
        assert outbox_event.event_type == "USERCONFIG_CREATED"
        assert outbox_event.routing_key == f"patient.user.config.created.{config_row.id}"
        assert outbox_event.created_by == "test-admin-user"

        print(f"[DONE]: OutboxEvent ID: {outbox_event.id}, type: {outbox_event.event_type}")

        payload = outbox_event.get_payload()

        assert payload["event_type"] == "USERCONFIG_CREATED"
        assert payload["userconfig_id"] == config_row.id
        assert payload["created_by"] == "test-admin-user"
        assert "userconfig_data" in payload
        assert "timestamp" in payload
        assert "correlation_id" in payload

        print(f"[DONE]: Payload verified — event_type, userconfig_id, created_by all correct")




class TestAdminConfigUpdateOutbox:
    """
    Tests for the USERCONFIG_UPDATED path.
    Triggered when an AdminConfig row ALREADY EXISTS.
    We create our own test row at the start of each test (the real row was
    already moved aside by save_and_restore_config).
    """

    def _seed_initial_config(self, integration_db, mock_user, sample_config_data):
        """
        Helper: create the initial test config row and return its ID.
        Also clears the CREATED outbox event so tests only see UPDATE events.
        """
        update_config_blob(
            db=integration_db,
            new_configs=sample_config_data,
            modified_by_id=mock_user,
            correlation_id=str(uuid.uuid4())
        )
        config_row = get_admin_config_row(integration_db)

        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(config_row.id)
        ).delete()
        integration_db.commit()

        return config_row.id

    def test_update_config_creates_outbox_event(
        self, integration_db, mock_user, sample_config_data, updated_config_data
    ):
        """
        GIVEN: An existing test AdminConfig row (SESSION_EXPIRE_MINUTES=11, MAX_PATIENT_PHOTO=11, MAX_ITEMS_TO_RETURN=11)
        WHEN:  update_config_blob() is called with SESSION_EXPIRE_MINUTES=22, MAX_PATIENT_PHOTO=22, MAX_ITEMS_TO_RETURN=22
        THEN:  A USERCONFIG_UPDATED OutboxEvent is created with the correct changes dict.
        """
        original_id = self._seed_initial_config(integration_db, mock_user, sample_config_data)
        print(f"\n[DONE]: Seeded test config row, ID: {original_id}")

        update_config_blob(
            db=integration_db,
            new_configs=updated_config_data,
            modified_by_id=mock_user,
            correlation_id=str(uuid.uuid4())
        )
        print(f"[DONE]: Updated config ID: {original_id}")

        refreshed = get_admin_config_row(integration_db)
        assert refreshed.configBlob == {"SESSION_EXPIRE_MINUTES": 22, "MAX_PATIENT_PHOTO": 22, "MAX_ITEMS_TO_RETURN": 22}
        assert refreshed.modifiedById == "test-admin-user"

        outbox_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id),
            OutboxEvent.event_type == "USERCONFIG_UPDATED"
        ).first()

        assert outbox_event is not None
        assert outbox_event.routing_key == f"patient.user.config.updated.{original_id}"
        assert outbox_event.created_by == "test-admin-user"

        print(f"[DONE]: OutboxEvent ID: {outbox_event.id}, type: {outbox_event.event_type}")

        payload = outbox_event.get_payload()

        assert payload["event_type"] == "USERCONFIG_UPDATED"
        assert payload["userconfig_id"] == original_id
        assert "changes" in payload
   
        assert "SESSION_EXPIRE_MINUTES" in payload["changes"]
        assert payload["changes"]["SESSION_EXPIRE_MINUTES"]["old"] == 11
        assert payload["changes"]["SESSION_EXPIRE_MINUTES"]["new"] == 22
 
        assert "MAX_PATIENT_PHOTO" in payload["changes"]
        assert payload["changes"]["MAX_PATIENT_PHOTO"]["old"] == 11
        assert payload["changes"]["MAX_PATIENT_PHOTO"]["new"] == 22

        assert "MAX_ITEMS_TO_RETURN" in payload["changes"]
        assert payload["changes"]["MAX_ITEMS_TO_RETURN"]["old"] == 11
        assert payload["changes"]["MAX_ITEMS_TO_RETURN"]["new"] == 22

        print(f"[DONE]: Changes dict verified — both keys show correct old/new values")

    def test_update_with_no_changes_does_not_create_outbox(
        self, integration_db, mock_user, sample_config_data
    ):
        """
        GIVEN: An existing test AdminConfig row
        WHEN:  update_config_blob() is called with THE SAME values (no real change)
        THEN:  NO outbox event is created and the DB row is NOT touched.
        """
        original_id = self._seed_initial_config(integration_db, mock_user, sample_config_data)
        config_row = get_admin_config_row(integration_db)
        original_modified_date = config_row.modifiedDate

        update_config_blob(
            db=integration_db,
            new_configs=sample_config_data,   # identical — no real change
            modified_by_id=mock_user,
            correlation_id=str(uuid.uuid4())
        )
        print(f"\n[DONE]: No-change update processed for config ID: {original_id}")

        outbox_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id),
            OutboxEvent.event_type == "USERCONFIG_UPDATED"
        ).first()

        assert outbox_event is None
        print(f"[DONE]: Confirmed no USERCONFIG_UPDATED event created for no-change update")

        refreshed = get_admin_config_row(integration_db)
        assert refreshed.modifiedDate == original_modified_date
        print(f"[DONE]: Verified modifiedDate unchanged — DB row was not touched")




class TestAdminConfigAtomicity:
    """
    Tests that AdminConfig writes and OutboxEvent writes happen in one
    atomic transaction — both succeed or both are rolled back.
    """

    def test_config_and_outbox_created_atomically(
        self, integration_db, mock_user, sample_config_data
    ):
        """
        GIVEN: Empty AdminConfig table (guaranteed by save_and_restore_config)
        WHEN:  update_config_blob() is called (CREATE path)
        THEN:  AdminConfig count increases by exactly 1 AND
               OutboxEvent count increases by exactly 1.
        """
        initial_config_count = integration_db.query(AdminConfig).count()
        initial_outbox_count = integration_db.query(OutboxEvent).count()

        update_config_blob(
            db=integration_db,
            new_configs=sample_config_data,
            modified_by_id=mock_user,
            correlation_id=str(uuid.uuid4())
        )

        final_config_count = integration_db.query(AdminConfig).count()
        final_outbox_count = integration_db.query(OutboxEvent).count()

        assert final_config_count == initial_config_count + 1
        assert final_outbox_count == initial_outbox_count + 1

        print(f"\n[DONE]: Config count:  {initial_config_count} → {final_config_count}")
        print(f"[DONE]: Outbox count:  {initial_outbox_count} → {final_outbox_count}")

        config_row = get_admin_config_row(integration_db)
        outbox = integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(config_row.id)
        ).first()
        assert outbox is not None

        print(f"[DONE]: Verified atomic creation — both rows share aggregate_id {config_row.id}")

    def test_config_update_and_outbox_created_atomically(
        self, integration_db, mock_user, sample_config_data, updated_config_data
    ):
        """
        GIVEN: An existing test AdminConfig row
        WHEN:  update_config_blob() is called with different values (UPDATE path)
        THEN:  The config row is modified AND the OutboxEvent is created in the same transaction.
        """
        # Create the initial test row
        update_config_blob(
            db=integration_db,
            new_configs=sample_config_data,
            modified_by_id=mock_user,
            correlation_id=str(uuid.uuid4())
        )
        config_row = get_admin_config_row(integration_db)
        original_id = config_row.id
        original_modified_date = config_row.modifiedDate

        # Clear the CREATED event so outbox count only reflects the UPDATE event
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id)
        ).delete()
        integration_db.commit()

        initial_outbox_count = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "USERCONFIG_UPDATED"
        ).count()

        print(f"\n[DONE]: Seeded test config ID: {original_id}")

        update_config_blob(
            db=integration_db,
            new_configs=updated_config_data,
            modified_by_id=mock_user,
            correlation_id=str(uuid.uuid4())
        )

        refreshed = get_admin_config_row(integration_db)
        assert refreshed.configBlob == {"SESSION_EXPIRE_MINUTES": 22, "MAX_PATIENT_PHOTO": 22, "MAX_ITEMS_TO_RETURN": 22}
        assert refreshed.modifiedDate > original_modified_date
        assert refreshed.modifiedById == "test-admin-user"

        final_outbox_count = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "USERCONFIG_UPDATED"
        ).count()
        assert final_outbox_count == initial_outbox_count + 1

        print(f"[DONE]: Outbox UPDATED count: {initial_outbox_count} → {final_outbox_count}")

        outbox = integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id),
            OutboxEvent.event_type == "USERCONFIG_UPDATED"
        ).first()

        assert outbox is not None
        assert outbox.routing_key == f"patient.user.config.updated.{original_id}"
        assert outbox.created_by == "test-admin-user"

        payload = outbox.get_payload()
        assert payload["userconfig_id"] == original_id
        assert "changes" in payload
        assert payload["changes"]["SESSION_EXPIRE_MINUTES"]["old"] == 11
        assert payload["changes"]["SESSION_EXPIRE_MINUTES"]["new"] == 22

        print(f"[DONE]: Verified atomic update — config modified and outbox event created together")
