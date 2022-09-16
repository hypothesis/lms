from typing import Optional, TypeVar

from lms.models import Region
from lms.validation import ValidationError

Model = TypeVar("Model")


def get_by_public_id(  # pylint:disable=too-many-arguments
    db, model: Model, public_id: str, region: Region, app="lms", type_="org"
) -> Optional[Model]:
    """
    Get a `model` by their public_id.

    Public IDs have a format like:
        region.app.type.id

    eg:
        us.lms.org.gkPHJPSRSHC7YWAYJ7s1LA

    :raises ValidationError: If the given ID doesn't have the right format
        or doesn't contain the expected constraints.
    """
    try:
        id_region, id_app, id_type, id_public_id = public_id.split(".")
    except ValueError as err:
        raise ValidationError(
            messages={"public_id": [f"{public_id} doesn't have the right format"]}
        ) from err

    if id_region != region.code:
        raise ValidationError(
            messages={
                "public_id": [
                    f"{id_region} doesn't match current region: {region.code}"
                ]
            }
        )

    if id_app != app:
        raise ValidationError(
            messages={"public_id": [f"{id_app} doesn't match app region: {app}"]}
        )

    if id_type != type_:
        raise ValidationError(
            messages={"public_id": [f"{id_type} doesn't match type: '{type_}'"]}
        )

    return db.query(model).filter_by(_public_id=id_public_id).one_or_none()
