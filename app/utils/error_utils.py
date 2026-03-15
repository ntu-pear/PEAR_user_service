from fastapi import HTTPException, status


def add_error(errors: list, field: str, message: str):
    errors.append({
        "loc": ["body", field],
        "msg": message,
    })


def raise_if_errors(errors: list, status_code: int = status.HTTP_400_BAD_REQUEST):
    if errors:
        raise HTTPException(
            status_code=status_code,
            detail=errors
        )


def field_error(field: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
    raise HTTPException(
        status_code=status_code,
        detail=[
            {
                "loc": ["body", field],
                "msg": message,
            }
        ]
    )