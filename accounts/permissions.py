"""
Central role/agency-scoping helpers, reused by every view in the project
that needs to restrict data to the logged-in user's agency. This is the
single source of truth for "who can see what" — individual views should
never re-implement this logic.
"""
from functools import wraps
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied

# Sentinel meaning "no restriction" — distinguishes a CEO (see everything)
# from a Manager/Staff with no agency assigned yet (see nothing, not
# everything). Using None for both would be ambiguous and dangerous.
UNRESTRICTED = object()


def get_employee(user):
    """Safe accessor — returns None if the user has no linked Employee
    record (e.g. a bare Django superuser with no Employee row)."""
    return getattr(user, 'employee', None)


def is_ceo(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    employee = get_employee(user)
    return employee is not None and employee.role == 'CEO'


def is_manager(user):
    employee = get_employee(user)
    return employee is not None and employee.role == 'MANAGER'


def is_staff_role(user):
    employee = get_employee(user)
    return employee is not None and employee.role == 'STAFF'


def get_agency_scope(user):
    """
    Returns one of:
      UNRESTRICTED   -> CEO/superuser: view all agencies, no filtering
      an Agency instance -> Manager/Staff: filter everything to this agency
      None            -> user has an Employee record but no agency assigned
                          (must NOT be treated as "no filter" — show a
                          clear message instead, never global data)
      False           -> user has no Employee record at all: no access
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return UNRESTRICTED
    employee = get_employee(user)
    if employee is None:
        return False
    if employee.role == 'CEO':
        return UNRESTRICTED
    return employee.agency  # Agency instance, or None if unassigned


def role_required(*roles):
    """
    View decorator restricting access to specific Employee.role values.
    Superusers always pass. Raises PermissionDenied (→ 403) rather than
    silently redirecting, per the spec's "never rely on frontend
    restrictions" requirement — this is enforced at the view itself.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('Login')
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            employee = get_employee(request.user)
            if employee is None or employee.role not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def scope_queryset(queryset, user, agency_field='agency'):
    """
    Applies get_agency_scope() to any queryset in one line. Raises
    PermissionDenied for users with no Employee record; returns the
    queryset filtered (or unfiltered for CEO) otherwise. Callers still
    need to handle the "employee has no agency assigned yet" case
    (scope is None) themselves, since the right message/UI differs
    per page — this deliberately doesn't paper over that state.
    """
    scope = get_agency_scope(user)
    if scope is False:
        raise PermissionDenied
    if scope is UNRESTRICTED:
        return queryset
    if scope is None:
        return queryset.none()
    return queryset.filter(**{agency_field: scope})