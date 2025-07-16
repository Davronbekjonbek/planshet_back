import logging
from ..models import Employee, NTochka

logger = logging.getLogger(__name__)


def get_employee_by_uuid(uuid):
    """
    Get employee by UUID.

    :param uuid: UUID of the employee
    :return: Employee instance or None if not found
    """
    try:
        return Employee.objects.get(uuid=uuid)
    except Employee.DoesNotExist:
        logger.error(f"Employee with UUID {uuid} not found")
        return None

def get_ntochka_by_uuid(uuid):
    """
    Get NTochka by UUID.

    :param uuid: UUID of the NTochka
    :return: NTochka instance or None if not found
    """
    try:
        return NTochka.objects.get(uuid=uuid)
    except NTochka.DoesNotExist:
        logger.error(f"NTochka with UUID {uuid} not found")
        return None