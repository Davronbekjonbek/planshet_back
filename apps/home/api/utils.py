from ..models import Employee

def get_employee_by_uuid(uuid):
    """
    Get employee by UUID.

    :param uuid: UUID of the employee
    :return: Employee instance or None if not found
    """
    try:
        return Employee.objects.get(uuid=uuid)
    except Employee.DoesNotExist:
        return None