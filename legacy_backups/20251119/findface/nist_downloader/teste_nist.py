import json
from idnetrr import idnetrr_civil
import base64
from functions import validate_cpf


if __name__ == '__main__':

    pessoa = idnetrr_civil.obter_biometria_idnet_por_rg(6425631)

    # # print(pessoa["numero_pessoa"])
    
    # infocidadao = obter_info_cidadao(numero_pessoa=pessoa["numero_pessoa"])

    # print(json.dumps(infocidadao, indent=4))

    # bin_foto = base64.b64decode(infocidadao["FOTO"])

    # bin_assinatura = base64.b64decode(infocidadao["SIGNATURE"])

    # bin_template_face = base64.b64decode(infocidadao["TEMPLATE_FACE"])

    # with open('foto.jpg', 'wb') as f:
    #     f.write(bin_foto)
    #     print("Foto gravada com sucesso.")

    # with open('assinatura.jpg', 'wb') as fa:
    #     fa.write(bin_assinatura)

    # with open('template_face.jpg', 'wb') as ft:
    #     ft.write(bin_template_face)
