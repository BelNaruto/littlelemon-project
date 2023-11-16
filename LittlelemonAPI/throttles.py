from rest_framework.throttling import UserRateThrottle

# For different endpoints calls, some endpoints can get 10 per min for example
class TenCallsPerMinute(UserRateThrottle):
    scope='ten'