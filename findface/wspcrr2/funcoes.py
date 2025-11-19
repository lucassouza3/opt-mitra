import json


def converter_card_para_pessoa(findface, origem):
    if "looks_like" in origem.keys():
        fotos = [origem.get("looks_like", {}).get("matched_object", "")]
    else:
        face_objects = findface.get_face_objects(card=origem["id"])["results"]
        face_object_id_list = [x["id"] for x in face_objects]
        fotos = face_object_id_list

    destino = {
        "bnmp": origem.get("meta", {}).get("bnmp", ""),
        "comentario": origem.get("comment", ""),
        "cpf": origem.get("meta", {}).get("cpf", ""),
        "documento": origem.get("meta", {}).get("documento", ""),
        "fotos": fotos,
        "id": origem.get("id", ""),
        "mae": origem.get("meta", {}).get("mae", ""),
        "match": {
            "foto": origem.get("looks_like", {}).get("matched_object", ""),
            "semelhanca": origem.get("looks_like", {}).get("confidence", 0.0)
        },
        "nacionalidade": origem.get("meta", {}).get("nacionalidade", ""),
        "nascimento": origem.get("meta", {}).get("data_nascimento", ""),
        "nome": origem.get("name", ""),
        "pai": origem.get("meta", {}).get("pai", ""),
        "passaporte": origem.get("meta", {}).get("passaporte", ""),
        "rnm": origem.get("meta", {}).get("rnm", "")
    }

    # Realiza os ajustes específicos para alguns campos, se necessário
    # Converte os IDs para nomes das listas
    destino["sistemas"] = [findface.get_watch_list_name_by_id(x) for x in origem.get("watch_lists", [])]
    
    return destino