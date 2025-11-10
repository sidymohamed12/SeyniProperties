# apps/employees/utils/mobile_utils.py
import json
import base64
from django.core.files.base import ContentFile
from django.utils import timezone
from django.conf import settings
from PIL import Image, ExifTags
import io

def process_mobile_image(image_data, max_size=(1920, 1080), quality=85):
    """
    Traite une image uploadée depuis mobile
    - Redimensionne si nécessaire
    - Corrige l'orientation EXIF
    - Compresse
    """
    try:
        # Si c'est du base64, le décoder
        if isinstance(image_data, str) and image_data.startswith('data:image'):
            format_info, img_str = image_data.split(';base64,')
            img_data = base64.b64decode(img_str)
            image = Image.open(io.BytesIO(img_data))
        else:
            image = Image.open(image_data)
        
        # Corriger l'orientation EXIF
        try:
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation':
                    break
            
            exif = image._getexif()
            if exif is not None:
                orientation_value = exif.get(orientation)
                if orientation_value == 3:
                    image = image.rotate(180, expand=True)
                elif orientation_value == 6:
                    image = image.rotate(270, expand=True)
                elif orientation_value == 8:
                    image = image.rotate(90, expand=True)
        except (AttributeError, KeyError, TypeError):
            pass
        
        # Redimensionner si nécessaire
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Convertir en RGB si nécessaire
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Sauvegarder avec compression
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        
        return ContentFile(output.read(), name='processed_image.jpg')
        
    except Exception as e:
        print(f"Erreur traitement image: {e}")
        return None

def generate_thumbnail(image_file, size=(300, 300)):
    """Génère une miniature d'une image"""
    try:
        image = Image.open(image_file)
        image.thumbnail(size, Image.Resampling.LANCZOS)
        
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=80)
        output.seek(0)
        
        return ContentFile(output.read(), name='thumbnail.jpg')
    except Exception:
        return None

def detect_mobile_device(request):
    """Détecte le type d'appareil mobile"""
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    
    if 'iphone' in user_agent or 'ipad' in user_agent:
        return 'ios'
    elif 'android' in user_agent:
        return 'android'
    elif 'windows phone' in user_agent:
        return 'windows'
    elif any(mobile in user_agent for mobile in ['mobile', 'tablet']):
        return 'mobile'
    else:
        return 'desktop'

def format_file_size(size_bytes):
    """Formate la taille de fichier pour affichage mobile"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def create_mobile_notification(user, title, message, action_url=None, icon='default'):
    """Crée une notification mobile"""
    notification_data = {
        'title': title,
        'message': message,
        'timestamp': timezone.now().isoformat(),
        'icon': icon,
        'action_url': action_url,
        'user_id': user.id
    }
    
    # Sauvegarder en base ou envoyer via push notification
    # À implémenter selon vos besoins
    
    return notification_data

def compress_audio(audio_file, target_bitrate=64):
    """Compresse un fichier audio pour mobile"""
    # À implémenter si nécessaire avec pydub ou ffmpeg
    return audio_file

def validate_mobile_upload(file, file_type='image'):
    """Valide un fichier uploadé depuis mobile"""
    errors = []
    
    # Vérifier la taille
    max_sizes = {
        'image': settings.MOBILE_SETTINGS['MAX_PHOTO_SIZE'],
        'audio': settings.MOBILE_SETTINGS['MAX_AUDIO_SIZE']
    }
    
    if file.size > max_sizes.get(file_type, max_sizes['image']):
        max_size_mb = max_sizes[file_type] / (1024 * 1024)
        errors.append(f'Le fichier est trop volumineux (max: {max_size_mb}MB)')
    
    # Vérifier le type
    allowed_types = {
        'image': settings.MOBILE_SETTINGS['ALLOWED_IMAGE_TYPES'],
        'audio': settings.MOBILE_SETTINGS['ALLOWED_AUDIO_TYPES']
    }
    
    if file.content_type not in allowed_types.get(file_type, allowed_types['image']):
        errors.append('Type de fichier non autorisé')
    
    return errors

def generate_qr_code(data, size=(200, 200)):
    """Génère un QR code pour mobile"""
    try:
        import qrcode
        from qrcode.image.styledpil import StyledPilImage
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img = img.resize(size, Image.Resampling.LANCZOS)
        
        output = io.BytesIO()
        img.save(output, format='PNG')
        output.seek(0)
        
        return ContentFile(output.read(), name='qrcode.png')
    except ImportError:
        return None
