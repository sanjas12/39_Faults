import sys
import importlib

def patch_reportlab():
    """Патч для reportlab для устранения ошибки usedforsecurity"""
    try:
        import reportlab.pdfbase.pdfdoc
        from reportlab.pdfbase.pdfdoc import PDFDocument
        
        # Сохраняем оригинальный метод
        original_init = PDFDocument.__init__
        
        def patched_init(self, *args, **kwargs):
            # Проверяем args на наличие usedforsecurity
            import hashlib
            try:
                # Проверяем, работает ли md5 с usedforsecurity
                hashlib.md5(b'test', usedforsecurity=False)
                # Если работает, используем оригинальный метод
                original_init(self, *args, **kwargs)
            except TypeError:
                # Если не работает, подменяем сигнатуру
                def wrapper(self, *args, **kwargs):
                    # Удаляем usedforsecurity из kwargs если есть
                    kwargs.pop('usedforsecurity', None)
                    # Также проверяем позиционные аргументы
                    new_args = []
                    for i, arg in enumerate(args):
                        if i == 0 and arg == 'usedforsecurity':
                            continue
                        new_args.append(arg)
                    original_init(self, *new_args, **kwargs)
                
                # Заменяем метод
                PDFDocument.__init__ = wrapper
                print("✅ ReportLab патч применён (обход usedforsecurity)")
        
        # Применяем патч
        PDFDocument.__init__ = patched_init
        print("✅ ReportLab патч успешно установлен")
        
    except Exception as e:
        print(f"⚠️ Не удалось применить патч: {e}")

# Применяем патч при импорте
patch_reportlab()