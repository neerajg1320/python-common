from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
import time


def azure_get_comutervision_client():
    key = 'be9dc1d6b084476b9a886546815739b0'
    endpoint = 'https://glassball-ocr-instance.cognitiveservices.azure.com/'

    return ComputerVisionClient(endpoint, CognitiveServicesCredentials(key))


def azure_ocr(image_file_path, computervision_client):
    # API Call
    with open(image_file_path, "rb") as image:
        read_response = computervision_client.read_in_stream(image, raw=True)

    # Get the operation location (URL with an ID at the end)
    read_operation_location = read_response.headers["Operation-Location"]

    # Grab the ID from the URL
    operation_id = read_operation_location.split("/")[-1]

    # Retrieve the results
    while True:
        read_result = computervision_client.get_read_result(operation_id)
        if read_result.status.lower() not in ['notstarted', 'running']:
            break
        time.sleep(1)

    # Get the detected text
    text_lines = []
    if read_result.status == OperationStatusCodes.succeeded:
        for page in read_result.analyze_result.read_results:
            for line in page.lines:
                # Print line
                # print(line.text)
                text_lines.append(line.text)

    return "\n".join(text_lines)


# azr_cv_client = azure_get_comutervision_client()
#
# text = azure_ocr("images/notes1.jpeg", azr_cv_client)
#
# print(text)
