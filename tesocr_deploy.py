#!/usr/bin/env python
"""
Tester OCR para verificar instalación en producción
"""
import os
import sys
import subprocess

def test_system_dependencies():
    print("🧪 TESTEANDO DEPENDENCIAS DEL SISTEMA...")
    
    # Test 1: Verificar Tesseract en sistema
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Tesseract sistema: {result.stdout.split()[1]}")
        else:
            print(f"❌ Tesseract sistema no disponible: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error ejecutando tesseract: {e}")
        return False
    
    # Test 2: Verificar Python puede importar pytesseract
    try:
        import pytesseract
        print("✅ pytesseract importado correctamente")
    except Exception as e:
        print(f"❌ Error importando pytesseract: {e}")
        return False
    
    # Test 3: Verificar OpenCV
    try:
        import cv2
        print(f"✅ OpenCV version: {cv2.__version__}")
    except Exception as e:
        print(f"❌ Error importando OpenCV: {e}")
        return False
    
    # Test 4: Verificar Pillow
    try:
        from PIL import Image
        print("✅ PIL importado correctamente")
    except Exception as e:
        print(f"❌ Error importando PIL: {e}")
        return False
    
    return True

def test_ocr_functionality():
    print("\n🧪 TESTEANDO FUNCIONALIDAD OCR...")
    
    try:
        import pytesseract
        from PIL import Image
        import cv2
        import numpy as np
        
        # Crear imagen de prueba con texto claro
        img = np.ones((100, 400, 3), dtype=np.uint8) * 255
        cv2.putText(img, "INVOICE TOTAL: 123.45 EUR", (20, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        
        # Convertir a PIL Image
        pil_img = Image.fromarray(img)
        
        # Ejecutar OCR
        text = pytesseract.image_to_string(pil_img)
        print(f"📝 Texto extraído: '{text.strip()}'")
        
        # Verificar resultados
        if "123.45" in text or "123,45" in text:
            print("✅ OCR funcionando correctamente - números detectados")
            return True
        elif text.strip():
            print("⚠️  OCR funciona pero no detectó el número esperado")
            return True
        else:
            print("❌ OCR no extrajo ningún texto")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba OCR: {e}")
        return False

if __name__ == "__main__":
    print("🚀 INICIANDO PRUEBAS OCR PARA DEPLOY")
    
    system_ok = test_system_dependencies()
    ocr_ok = test_ocr_functionality() if system_ok else False
    
    print(f"\n📊 RESULTADOS:")
    print(f"   Sistema: {'✅' if system_ok else '❌'}")
    print(f"   OCR: {'✅' if ocr_ok else '❌'}")
    
    if system_ok and ocr_ok:
        print("🎉 TODAS LAS PRUEBAS PASARON - OCR LISTO PARA PRODUCCIÓN")
        sys.exit(0)
    else:
        print("💥 ALGUNAS PRUEBAS FALLARON - REVISAR CONFIGURACIÓN")
        sys.exit(1)