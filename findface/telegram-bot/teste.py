from findface_multi.findface import *
import requests


filepath = r'C:\Users\leonardo.lad\Downloads\Leo1.jpg'

login_data = {'uuid': 'telegram-bot'}
with FindfaceMultiAPI(base_url='https://sdf0889.pf.gov.br', username='s_consulta', password='botconsulta2024', login_data=login_data) as findface:

    data = { "face": {} }
    detection = findface.detect(filepath, attributes=data)

    cards_humans = []
    for face in detection["objects"]["face"]:

        filters = {'looks_like': f'detection:{face["id"]}'}
        response = findface.list_human_cards(filters)
        if len(response["results"]) > 0:
            cards_humans.extend(response["results"])

    if len(cards_humans) > 0:

        for card in cards_humans:

            card_id = card["id"]

            data = {"card": [card_id]}
            face_objects = findface.get_faces(query_params=data)["results"]

            for face_object in face_objects:
                url_foto = face_object["source_photo"]

                response = requests.get(url_foto, verify=False)

                if 200 <= response.status_code < 300:
                    pass

                else:
                    print(response.text)

        
