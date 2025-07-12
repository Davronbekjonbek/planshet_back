from ..models import TochkaProduct

def get_tochka_product_by_uuid(uuid):
    """
    Retrieve a TochkaProduct instance by its UUID.

    :param uuid: UUID of the TochkaProduct.
    :return: TochkaProduct instance or None if not found.
    """
    try:
        return TochkaProduct.objects.get(uuid=uuid, is_active=True)
    except TochkaProduct.DoesNotExist:
        return None