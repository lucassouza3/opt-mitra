from findface_multi.findface_multi import FindfaceConnection, FindfaceException, FindfaceMulti
import os
import json
from datetime import datetime
from pathlib import Path

url = os.environ["FINDFACE_URL"]
usuario = os.environ["FINDFACE_USER"]
senha = os.environ["FINDFACE_PASSWORD"]

agenda_path = Path(__file__).with_name("tarefas_agendadas.json")

def load_agenda(path: Path) -> dict:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        print(f"Arquivo de agenda '{path}' não encontrado.")
        raise SystemExit(1)

    sanitized_lines = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        if "#" in line:
            line = line.split("#", 1)[0]
        sanitized_lines.append(line)

    raw_content = "\n".join(sanitized_lines).strip()
    if not raw_content:
        print(f"Arquivo de agenda '{path}' está vazio.")
        raise SystemExit(1)

    try:
        return json.loads(raw_content)
    except json.JSONDecodeError as exc:
        backup = path.with_suffix(".json.corrompido")
        backup.write_text(raw_content, encoding="utf-8")
        print(f"Agenda inválida. Cópia gerada em '{backup}'. Erro: {exc}")
        raise SystemExit(1)

agenda = load_agenda(agenda_path)

with FindfaceConnection(base_url=url, username=usuario, password=senha) as findface_connection:

    findface = FindfaceMulti(findface_connection)

    agora = datetime.now()
    dia_da_semana = agora.weekday()
    hora_atual = agora.time()

    # print("Dia da semana:", dia_da_semana)  # Debug

    # GRUPOS DE CAMERAS
    camera_groups = agenda["camera_groups"]
    for tarefa in camera_groups:
        # print(tarefa)
        if dia_da_semana in tarefa["dias_da_semana"]:
            hora_inicial = datetime.strptime(tarefa["hora_inicial"], "%H:%M").time()
            hora_final = datetime.strptime(tarefa["hora_final"], "%H:%M").time()

            # Obtem o nome do grupo de câmera
            resposta_nome = findface.get_camera_group_by_id(tarefa["id"])
            if resposta_nome:
                nome_grupo_de_cameras = resposta_nome["name"]

                if hora_inicial <= hora_atual <=hora_final:
                    status = tarefa["ativo"]
                else:
                    status = not tarefa["ativo"]

                resposta = findface.update_camera_group(tarefa["id"], active=status)
                if resposta:
                    print(f"Status do grupo de câmeras '{nome_grupo_de_cameras}' alterado para: {status}")

    # CAMERAS
    camera_groups = agenda["cameras"]
    for tarefa in camera_groups:
        # print(tarefa)
        if dia_da_semana in tarefa["dias_da_semana"]:
            hora_inicial = datetime.strptime(tarefa["hora_inicial"], "%H:%M").time()
            hora_final = datetime.strptime(tarefa["hora_final"], "%H:%M").time()

            # Obtem o nome do grupo de câmera
            resposta_nome = findface.get_camera_by_id(tarefa["id"])
            if resposta_nome:
                nome_camera = resposta_nome["name"]

                if hora_inicial <= hora_atual <=hora_final:
                    status = tarefa["ativo"]
                else:
                    status = not tarefa["ativo"]

                resposta = findface.update_camera(tarefa["id"], active=status)
                if resposta:
                    print(f"Status da câmera '{nome_camera}' alterado para: {status}")

    # WATCH LISTS
    watch_lists = agenda["watch_lists"]
    for tarefa in watch_lists:
        if dia_da_semana in tarefa["dias_da_semana"]:
            hora_inicial = datetime.strptime(tarefa["hora_inicial"], "%H:%M").time()
            hora_final = datetime.strptime(tarefa["hora_final"], "%H:%M").time()


            # Obtem o nome do grupo de câmera
            nome_watch_list = findface.get_watch_list_name_by_id(tarefa["id"])
            if nome_watch_list:
                if hora_inicial <= hora_atual <=hora_final:
                    status = tarefa["ativo"]
                else:
                    status = not tarefa["ativo"]

                resposta = findface.update_watch_list(tarefa["id"], active=status)
                if resposta:
                    print(f"Status da lista '{nome_watch_list}' alterado para: {status}")

