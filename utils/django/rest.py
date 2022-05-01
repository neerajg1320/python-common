# duplicated from worker_mapper_loader
def get_mock_request():
    # Create a fake request object
    # from rest_framework.test import APIRequestFactory
    # factory = APIRequestFactory()
    # request = factory.post('/api/portfolio/transactions')
    # request.user = file.user

    request = lambda: None
    return request
