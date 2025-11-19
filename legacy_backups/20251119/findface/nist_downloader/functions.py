from unidecode import unidecode
import io
import filetype
from datetime import datetime
import copy
import csv
from io import BytesIO
from PIL import Image
from pathlib import Path
import imageio
import numpy as np
import imagecodecs
import wsq


def convert_to_wsq(input_data):
    
    # Determine the type of the input_data and handle accordingly
    if isinstance(input_data, str):  # Filepath
        # Open the image from a filepath
        img = Image.open(input_data)
    elif isinstance(input_data, io.BytesIO):  # BytesIO object
        # Open the image from a BytesIO object
        img = Image.open(input_data)
    elif isinstance(input_data, bytes):  # Bytes
        # Open the image from a byte string
        img = Image.open(io.BytesIO(input_data))
    else:
        raise ValueError(f"Unsupported input type {type(input_data)}. Must be filepath (str), io.BytesIO, or bytes.")

    # Convert image to grayscale
    with img:
        # Convert to grayscale image (important)
        new_file = io.BytesIO()
        img = img.convert("L")
        img.save(new_file, 'WSQ')
        
        return new_file.getvalue()


def convert_to_jpeg(input_data):
    # Determine the type of the input_data and handle accordingly
    if isinstance(input_data, str):  # Filepath
        # Open the image from a filepath
        img = Image.open(input_data)
    elif isinstance(input_data, io.BytesIO):  # BytesIO object
        # Open the image from a BytesIO object
        img = Image.open(input_data)
    elif isinstance(input_data, bytes):  # Bytes
        # Open the image from a byte string
        img = Image.open(io.BytesIO(input_data))
    else:
        raise ValueError(f"Unsupported input type '{type(input_data)}'. Must be filepath (str), io.BytesIO, or bytes.")

    # Convert image to grayscale
    with img:
        new_file = io.BytesIO()
        img.save(new_file, 'JPEG', quality=95)
        
        return new_file.getvalue()


def formata_nacionalidade(value):

    if value is None:
        return None
    
    file_path = Path(__file__).parent / 'TB_PAIS.csv'
    dict_codigo_nome_pais = {}
    dict_nome_codigo_pais = {}

    with open(file_path, mode='r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        paises = []
        for row in csv_reader:
            if row[0] == 'CD_PAIS':  # Exclui a linha cabeçalho
                continue

            codigo_pais = formata_nome(row[0])
            nome_pais = formata_nome(row[1])

            dict_codigo_nome_pais[codigo_pais] = nome_pais
            # dict_nome_codigo_pais[nome_pais] = codigo_pais

    nacionalidade = formata_nome(value)

    if nacionalidade.isdigit():
        try:
            nacionalidade = dict_codigo_nome_pais[value]
        except Exception as e:
            nacionalidade = None
    elif nacionalidade not in dict_codigo_nome_pais.values():
        nacionalidade = None

    return nacionalidade


def formata_sexo(sexo):
    new_value = None
    if str(sexo).isdigit():
        if sexo == '1':
            new_value = 'M'
        elif sexo == '2':
            new_value = 'F'
        elif sexo == '3':
            new_value = 'O'
        else:
            new_value = None
    elif sexo.upper() in ['M', 'F', 'O']:
        new_value = sexo
    elif sexo.strip().upper() == 'MASCULINO':
        new_value = 'M'
    elif sexo.strip().upper() == 'FEMININO':
        new_value = 'F'

    return formata_nome(new_value)


def formata_nome(s):
    if s is None:
        return None
 
    # Ensure that it's string type
    if not isinstance(s, str):
        raise TypeError("Input must be a string")

    # Remove spaces at the beginning and end
    s = s.strip()

    # If the remaining string is empty, set it to None
    if not s:
        return None

    # Remove all double spaces between words
    s = ' '.join(s.split())

    # Uppercase all letters
    s = s.upper()

    # Convert all letters to ASCII representation
    s = unidecode(s)

    return s


def formata_documento(s):
    if s is None:
        return None

    # Ensure that it's string type
    if not isinstance(s, (str)):
        raise TypeError("Input must be a string")


    # Remove spaces at the beginning and end
    s = s.strip()

    # If the remaining string is empty, set it to None
    if not s:
        return None

    # Remove all characters that are not alpha or digit
    s = ''.join(filter(str.isalnum, s))

    # Convert all letters to ASCII representation
    s = unidecode(s)

    # Uppercase all letters
    s = s.upper()

    return s


def formata_data_nascimento(date_input):
    """
    Formats a given date input (datetime object or string in various formats) to a string in '%Y-%m-%d' format.

    Parameters:
    - date_input (datetime or str): The date to format, which can be a datetime object or a string in one of the following formats:
      '%Y-%m-%d', '%Y%m%d', '%d-%m-%Y', or '%d%m%Y'.

    Returns:
    - str: The date formatted in '%Y-%m-%d' format if the input is valid. Returns None if the date is invalid.
    """
    
    # Define the list of acceptable string date formats
    date_formats = [r'%Y-%m-%d', r'%Y%m%d', r'%d-%m-%Y', r'%d%m%Y', r'%d/%m/%Y',]
    
    # If input is already a datetime object, format it to the desired format
    if isinstance(date_input, datetime):
        return date_input.strftime('%Y-%m-%d')
    
    # If input is a string, try parsing it with the acceptable formats
    elif isinstance(date_input, str):
        for fmt in date_formats:
            try:
                # Parse the date string using the current format
                parsed_date = datetime.strptime(date_input, fmt)
                # If successful, return the date in the desired format
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                pass
    
    # If no formats match
    # raise ValueError(f'Data de nascimento "{date_input}" inválida.')
    return None


def preencher_zeros(valor):
    # Converte o valor para string, se não for uma já
    valor_str = str(valor)
    # Preenche com zeros à esquerda até completar 11 caracteres
    return valor_str.zfill(11)


def validate_cpf(numbers: str | int) -> str:
    """
    Validates a Brazilian CPF number for correct formatting and checks the digits according to the CPF rules.
    
    The CPF (Cadastro de Pessoas Físicas) is a Brazilian individual taxpayer registry identification. This function
    checks if the provided CPF is valid by ensuring it contains 11 digits, is not a sequence of identical numbers,
    and both of its verifying digits are correct according to the standard CPF formula.
    
    Parameters:
    - numbers (str | int): The CPF number to validate. It can be provided as a string or integer. Strings
      can contain non-digit characters, which will be ignored.
    
    Returns:
    - str: The validated CPF number as a string of digits if it is valid.
    - bool: False if the CPF number is invalid.
    - None: If the input is not a string or an integer, or if it's an empty or whitespace-only string.
    
    Examples:
    - validate_cpf("123.456.789-09") -> False (assuming it's an invalid CPF number)
    - validate_cpf(12345678909) -> "12345678909" (assuming it's a valid CPF number)
    - validate_cpf("111.111.111-11") -> False (invalid because it's a sequence of identical numbers)
    """
    
    if isinstance(numbers, int):
        numbers = str(numbers)

    numbers = preencher_zeros(numbers)

    if isinstance(numbers, str) and numbers is not None and len(numbers.strip()) > 0:
        cpf = [int(char) for char in numbers if char.isdigit()]
        if len(cpf) != 11:
            return False
        if all(cpf[i] == cpf[i + 1] for i in range(0, len(cpf) - 1)):
            return False
        for i in range(9, 11):
            value = sum((cpf[num] * ((i + 1) - num) for num in range(0, i)))
            digit = ((value * 10) % 11) % 10
            if digit != cpf[i]:
                return False    
        return ''.join(str(x) for x in cpf)


def is_image(file: str | bytes | io.BytesIO) -> bool:
    """
    Determines whether the provided file is an image by checking its MIME type.
    
    This function reads the content of the file, which can be specified as a file path, a bytes object,
    or an io.BytesIO object. It uses the 'filetype.guess' function to determine the MIME type of the file content.
    If the MIME type starts with 'image/', the file is considered an image and the function returns True. Otherwise,
    it returns False.
    
    Parameters:
    - file (str | bytes | io.BytesIO): The file to be checked. This can be:
        - A string representing a file path to the file on disk.
        - A bytes object containing the file's content.
        - An io.BytesIO object wrapping the file's content in a file-like object.
    
    Returns:
    - bool: True if the file is an image, False otherwise.
    
    Raises:
    - ValueError: If the 'file' parameter is not one of the accepted types.
    """
    if isinstance(file, str):
        with open(file, 'rb') as f:
            file_content = f.read()    
    elif isinstance(file, io.BytesIO):
        file_content = file.getvalue()
    elif isinstance(file, bytes):
        file_content = file
    else:
        raise TypeError(f'Tipo <{type(file)}> inválido para "file". Esperado tipo <str>|<bytes>|<io.BytesIO>.')

    kind = filetype.guess(file_content)
    if kind is not None and kind.mime.startswith('image/'):
        return True
    
    return False
    

def is_valid_wsq(file: str | bytes | io.BytesIO) -> bool:
    """
    Determines whether the provided file is a WSQ (Wavelet Scalar Quantization) file based on its content.
    
    This function reads the content of the file, which can be specified as a file path, a bytes object,
    or an io.BytesIO object. It then checks the start of the file content for specific markers that indicate
    it is a WSQ file. Note: This example uses a hypothetical marker for illustration. Actual WSQ file validation
    requires more detailed analysis of the file structure.
    
    Parameters:
    - file (str | bytes | io.BytesIO): The file to be checked. This can be:
        - A string representing a file path to the file on disk.
        - A bytes object containing the file's content.
        - An io.BytesIO object wrapping the file's content in a file-like object.
    
    Returns:
    - bool: True if the file is a WSQ file, False otherwise.
    
    Raises:
    - ValueError: If the 'file' parameter is not one of the accepted types.
    """
    if isinstance(file, str):
        with open(file, 'rb') as f:
            file_content = f.read()    
    elif isinstance(file, io.BytesIO):
        file_content = file.getvalue()
    elif isinstance(file, bytes):
        file_content = file
    else:
        raise TypeError(f'Tipo <{type(file)}> inválido para "file". Esperado tipo <str>|<bytes>|<io.BytesIO>.')


    file_stream = BytesIO(file_content)

    # Go to the start of the file stream
    file_stream.seek(0)
    
    # Read the first few bytes to check for WSQ markers
    start_bytes = file_stream.read(4)
    
    # Example check for specific bytes; adjust based on more reliable markers if available
    # This is a placeholder; real WSQ validation would require more detailed analysis
    if start_bytes[:2] == b'\xff\xa0':  # Hypothetical marker; actual WSQ files do not have a simple magic number
        return True

    return False


def convert_wsq_to_jpg(file: str | bytes | io.BytesIO) -> bytes:
    """
    Converts an image from WSQ (Wavelet Scalar Quantization) format to JPEG format.
    
    This function reads the content of the file, which can be specified as a file path, a bytes object,
    or an io.BytesIO object. It then opens the image using PIL (Pillow) and converts it to JPEG format,
    returning the JPEG image as a bytes object.
    
    Parameters:
    - file (str | bytes | io.BytesIO): The WSQ file to be converted. This can be:
        - A string representing a file path to the file on disk.
        - A bytes object containing the file's content.
        - An io.BytesIO object wrapping the file's content in a file-like object.
    
    Returns:
    - bytes: The content of the converted JPEG image as a bytes object.
    
    Raises:
    - ValueError: If the 'file' parameter is not one of the accepted types.
    """
    if isinstance(file, str):
        with open(file, 'rb') as f:
            file_content = f.read()    
    elif isinstance(file, io.BytesIO):
        file_content = file.getvalue()
    elif isinstance(file, bytes):
        file_content = file
    else:
        raise TypeError(f'Tipo <{type(file)}> inválido para "file". Esperado tipo <str>|<bytes>|<io.BytesIO>.')        

    # Use PIL to open the image. Note: Direct WSQ to JPEG conversion assumes PIL can handle WSQ format,
    # which may require additional plugins or libraries.
    image_stream = BytesIO(file_content)
    pil_img = Image.open(image_stream)

    # Convert the image to JPEG
    jpg_stream = BytesIO()
    pil_img.save(jpg_stream, "JPEG")

    # Return the JPEG image as bytes
    jpg_stream.seek(0)
    return jpg_stream.getvalue()


def formata_imagem(file: str | bytes | io.BytesIO) -> bytes:
    """
    Formats an image file by converting it from WSQ format to JPEG if necessary and
    checks whether the file is a valid image. If the file is not a valid image, it raises an error.
    
    Parameters:
    - file (str | bytes | io.BytesIO): The file to format. This can be a file path (str),
      the content of the file in bytes, or an io.BytesIO object containing the file's content.
    
    Returns:
    - bytes: The content of the formatted image file as a bytes object. If the file was originally
      in WSQ format, it will be converted to JPEG format.
    
    Raises:
    - ValueError: If the input 'file' is not a valid type or if the file content is not a valid image.
    """
    
    # Read the file content based on its type
    if isinstance(file, str):
        with open(file, 'rb') as f:
            file_content = f.read()    
    elif isinstance(file, io.BytesIO):
        file_content = file.getvalue()
    elif isinstance(file, bytes):
        file_content = file
    else:
        raise TypeError(f'Tipo <{type(file)}> inválido para "file". Esperado tipo <str>|<bytes>|<io.BytesIO>.')

    # Convert WSQ to JPEG if necessary
    if is_valid_wsq(file_content):
        file_content = convert_wsq_to_jpg(file_content)
    
    # Validate the final image
    if not is_image(file_content):
        raise ValueError('Arquivo não é uma imagem válida.')

    return file_content


def extract_faces_from_nist(nist):
    if not isinstance(nist, NIST):
        raise TypeError(f'Tipo <{type(nist)}> inválido para "nist". Esperado tipo <NIST>.')

    faces = []
    ntypes = nist.get_ntype()
    # Foto facial
    if 10 in ntypes:
        idcs_nytpe10 = nist.get_idc(ntype=10)
        for idc in idcs_nytpe10:
            face = nist.get_field('10.999', idc=idc)

            if not is_image(face):
                raise Exception('Aquivo não é uma imagem.')

            faces.append(face)
    else:
        print("Nenhum registro Tipo 10 (face) encontrado no NIST.")

    return faces


def clean_card_data(data):
    """
    Recursively removes all keys with None or empty string values from a dictionary. Additionally,
    removes the key 'comment' if it is present in any level of the dictionary.

    Parameters:
    - data (dict): The dictionary to clean.

    Returns:
    - dict: A new dictionary with the specified keys removed.
    """

    def recursive_clean(obj):
        """Recursively cleans the dictionary or list by removing specified values and keys."""
        if isinstance(obj, dict):
            return {k: recursive_clean(v) for k, v in obj.items() if v is not None and v != '' and k != 'comment'}
        elif isinstance(obj, list):
            return [recursive_clean(item) for item in obj]
        else:
            return obj

    cleaned_data = recursive_clean(data)
    return cleaned_data


def prune_fields_not_in_dictB(dictA, dictB, parent_key=''):
    """
    Recursively removes all fields from dictA that are not present in dictB. Raises an exception if a field in dictB
    is not present in dictA, including checking nested dictionaries.

    Parameters:
    - dictA (dict): The dictionary from which fields will be removed.
    - dictB (dict): The dictionary used as a template to determine which fields should remain in dictA.
    - parent_key (str, optional): Used for tracking the nested path in recursive calls for error messaging.

    Returns:
    - dict: A new dictionary based on dictA with only the fields that are present in dictB.

    Raises:
    - FieldNotFoundException: If a field in dictB is not present in dictA.
    """
    pruned_dict = {}

    for key in dictB:
        if key not in dictA:
            full_key = f"{parent_key}.{key}" if parent_key else key
            raise Exception(full_key)

    for key in dictA:
        if key in dictB:
            if isinstance(dictA[key], dict) and isinstance(dictB[key], dict):
                pruned_dict[key] = prune_fields_not_in_dictB(dictA[key], dictB[key], parent_key=key if not parent_key else f"{parent_key}.{key}")
            else:
                pruned_dict[key] = dictA[key]

    return pruned_dict


class MergeException(Exception):
    def __init__(self, field):
        message = f"Conflict detected at '{field}' with different non-empty values in dictA and dictB."
        super().__init__(message)


def merge_pessoa_card(dados_pessoa, dados_card, excluded_fields=['comment', 'active'], force_merge_fields=['comment', 'active']):
    """
    Merges fields from dados_pessoa into a copy of dados_card based on specific rules, with support for excluding certain fields
    from the merge process and forcing the merge of specific fields even if the copy of dados_card already has a value.

    Parameters:
    - dados_pessoa (dict): The dictionary containing person's data to merge from.
    - dados_card (dict): The dictionary containing card's data to merge into.
    - excluded_fields (list of str, optional): Fields that should not be merged.
    - force_merge_fields (list of str, optional): Fields where dados_pessoa's value should overwrite the copy of dados_card's
      value even if it already exists.

    Returns:
    - dict or None: Returns a modified copy of dados_card with merged fields if any merge occurred, otherwise None if
      no fields were merged or if any non-excludable conflicting values are found.
    """
    # Create a deep copy of dados_card to work with
    dados_card_copy = copy.deepcopy(dados_card)

    if excluded_fields is None:
        excluded_fields = []
    if force_merge_fields is None:
        force_merge_fields = []

    merged = False

    # Merge top-level fields into the copy
    for key, value_pessoa in dados_pessoa.items():
        if key in excluded_fields or key == 'meta':
            continue  # Skip excluded fields and handle 'meta' separately

        if key in force_merge_fields or (dados_card_copy.get(key) in [None, ""] or value_pessoa not in [None, ""]):
            if dados_card_copy.get(key) != value_pessoa and dados_card_copy.get(key) not in [None, ""] and key not in force_merge_fields:
                return None  # Conflict found and not a force merge field
            dados_card_copy[key] = value_pessoa
            merged = True

    # Merge 'meta' fields into the copy if present
    if 'meta' in dados_pessoa and 'meta' not in excluded_fields:
        meta_pessoa = dados_pessoa['meta']
        meta_card_copy = dados_card_copy.get('meta', {})
        
        for meta_key, meta_value in meta_pessoa.items():
            if meta_key in excluded_fields:
                continue  # Skip excluded 'meta' fields

            if meta_key in force_merge_fields or (meta_card_copy.get(meta_key) in [None, ""] or meta_value not in [None, ""]):
                if meta_card_copy.get(meta_key) != meta_value and meta_card_copy.get(meta_key) not in [None, ""] and meta_key not in force_merge_fields:
                    return None  # Conflict found and not a force merge field
                meta_card_copy[meta_key] = meta_value
                merged = True
        
        dados_card_copy['meta'] = meta_card_copy
 
    return dados_card_copy if merged else None


def compare_dicts(dictA, dictB):
    """
    Recursively compares two dictionaries to check if all keys and values are equal.

    Parameters:
    - dictA (dict): The first dictionary for comparison.
    - dictB (dict): The second dictionary for comparison.

    Returns:
    - bool: True if all keys and values are equal, False otherwise.
    """
    if dictA.keys() != dictB.keys():
        return False  # Different sets of keys

    for key in dictA:
        valA = dictA[key]
        valB = dictB[key]

        if isinstance(valA, dict) and isinstance(valB, dict):
            if not compare_dicts(valA, valB):
                return False
        elif valA != valB:
            return False

    return True


def card_data_to_filters(card_data: dict, excluded_fields: list = ['nacionalidade', 'documento']) -> dict:
    """
    Converts card data into filter criteria, excluding specified fields.

    Parameters:
    - card_data (dict): The source card data to be converted.
    - excluded_fields (list, optional): A list of field names to be excluded from the returned filters.

    Returns:
    - dict: A dictionary of filter criteria based on the card data, excluding specified fields.

    Raises:
    - TypeError: If the input card_data is not a dictionary.
    """
    if not isinstance(card_data, dict):
        raise TypeError(f'Tipo <{type(card_data)}> inválido para "card_data". Esperado tipo <dict>.')

    card_data = clean_card_data(card_data)  # Assuming clean_card_data is a function defined elsewhere

    filters = {}

    # Add 'name_contains' and 'watch_lists' if not in excluded_fields
    if "name" not in excluded_fields:
        filters["name_contains"] = card_data["name"]
    if "watch_lists" not in excluded_fields:
        filters["watch_lists"] = card_data["watch_lists"]

    # Add items from 'meta', excluding specified fields
    for key, value in card_data["meta"].items():
        if key not in excluded_fields:
            filters[key] = value

    return filters

def find_object_face_with_highest_quality_score(faces):
    """
    Finds the face object with the highest detection score from a list of face objects.

    Parameters:
    - faces (list): A list of face objects, each containing an 'id', 'bbox', 'detection_score', 'low_quality', and 'features'.

    Returns:
    - dict: The face object with the highest detection score. Returns None if the list is empty.
    """
    if not faces:
        return None

    highest_score_face = 0
    highest_face = None
    for face in faces:
        if face["detection_score"] > highest_score_face:
            highest_score_face = face["detection_score"]
            highest_face = face

    return highest_face


def find_biggest_bbox(faces):
    """
    Finds the face with the biggest bounding box (bbox) from a list of face objects.

    Parameters:
    - faces (list): A list of face objects, each containing an 'id' and a 'bbox' with 'left', 'top', 'right', 'bottom' coordinates.

    Returns:
    - dict: The face object with the biggest bounding box. Returns None if the list is empty.
    """
    if not faces:
        return None

    def bbox_area(face):
        """Calculates the area of a face's bounding box."""
        bbox = face["bbox"]
        width = bbox["right"] - bbox["left"]
        height = bbox["bottom"] - bbox["top"]
        return width * height

    # Find the face with the maximum bounding box area
    biggest_face = max(faces, key=bbox_area)
    
    return biggest_face


def compara_pessoa_card(dados_pessoa, dados_card, excluded_fields=['comment', 'documento', 'active']):
    """
    Compares two dictionaries representing a person and a card to determine if they represent the same entity based on specific fields,
    and additionally compares all other fields for equality, excluding any specified in 'excluded_fields' and ignoring differences
    where one side has None or empty string value unless both sides are not None or empty for other fields.
    
    A match occurs if any of the following conditions are met:
    - 'cpf', 'rnm', 'passaporte', or 'bnmp' fields are equal in both dictionaries, or
    - 'name', 'data_nascimento', and 'mae' fields are all equal in both dictionaries, or
    - 'name', 'data_nascimento', and 'pai' fields are all equal in both dictionaries,
    - and all remaining fields, excluding any specified in 'excluded_fields', and excluding if one of dict sides has None or empty string value
    
    Parameters:
    - dados_pessoa (dict): The dictionary containing person's data.
    - dados_card (dict): The dictionary containing card's data.
    - excluded_fields (list of str, optional): Field names to exclude from the remaining fields comparison.

    Returns:
    - dict or None: Returns dados_card if a match is found based on the specified rules; otherwise, returns None.
    """
    if excluded_fields is None:
        excluded_fields = []

    # Initial field checks based on critical identification fields
    meta_pessoa = dados_pessoa.get('meta', {})
    meta_card = dados_card.get('meta', {})
    for field in ['cpf', 'rnm', 'passaporte', 'bnmp']:
        if (meta_pessoa.get(field) and meta_card.get(field)) and meta_pessoa[field] == meta_card[field]:
            break
    else:  # Check for composite identification fields if no direct match is found
        if not (
            dados_pessoa.get('name') == dados_card.get('name') and
            meta_pessoa.get('data_nascimento') == meta_card.get('data_nascimento') and
            (meta_pessoa.get('mae') == meta_card.get('mae') or meta_pessoa.get('pai') == meta_card.get('pai'))
        ):
            return None

    # Compare remaining fields for equality, ignoring None or empty strings unless critical
    all_keys = set(dados_pessoa.keys()).union(dados_card.keys()) - set(excluded_fields)
    for key in all_keys:
        value_pessoa = dados_pessoa.get(key)
        value_card = dados_card.get(key)

        # Special handling for 'meta' dictionary
        if key == 'meta':
            meta_keys = set(meta_pessoa.keys()).union(meta_card.keys()) - set(excluded_fields)
            for meta_key in meta_keys:
                if meta_pessoa.get(meta_key) != meta_card.get(meta_key) and \
                   meta_pessoa.get(meta_key) not in [None, ''] and meta_card.get(meta_key) not in [None, '']:
                    return None
        elif key not in excluded_fields and value_pessoa != value_card:
            if value_pessoa not in [None, ''] and value_card not in [None, '']:
                return None

    # If all checks pass
    return dados_card


def diff_dicts(dictA, dictB, parent_key=''):
    """
    Recursively compares two dictionaries and returns a list of keys where the values in dictA differ from dictB.

    Parameters:
    - dictA (dict): The first dictionary to compare.
    - dictB (dict): The second dictionary to compare.
    - parent_key (str): Used internally to track the key path for nested dictionaries.

    Returns:
    - list: A list of keys indicating where values in dictA differ from those in dictB.
    """
    differing_keys = []

    for key, valueA in dictA.items():
        # Construct the full key path for nested dictionaries
        full_key = f"{parent_key}.{key}" if parent_key else key

        if key not in dictB:
            differing_keys.append(full_key)
        else:
            valueB = dictB[key]
            if isinstance(valueA, dict) and isinstance(valueB, dict):
                # Recursively compare nested dictionaries
                differing_keys.extend(diff_dicts(valueA, valueB, full_key))
            elif valueA != valueB:
                differing_keys.append(full_key)

    # Check for keys in dictB that are not in dictA
    for key in dictB:
        full_key = f"{parent_key}.{key}" if parent_key else key
        if key not in dictA:
            differing_keys.append(full_key)

    return differing_keys


def nist_to_card(nist):
    if not isinstance(nist, dict):
        raise TypeError(f'Tipo <{type(nist)}> inválido para "nist". Esperado tipo <dict>.')


def formata_nome_base_origem(value):
    # Corrige o nome da base de origem para o formato UF/NOME-DA-BASE quando as bases forem da PF
    if '/' not in value and value in ['SISMIGRA', 'SINPA', 'BNMP']:
        value = 'PF/' + value

    return value


def obter_sem_imagem():
    sem_imagem_filepath = Path(__file__).parent / 'SemImagem.png'
    with open(sem_imagem_filepath, 'rb') as rf:
        sem_imagem_bin = rf.read()

    return sem_imagem_bin
