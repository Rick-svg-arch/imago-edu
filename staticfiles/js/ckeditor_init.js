function initializeCKEditor(elementId, configName) {
    console.log('Inicializando CKEditor para:', elementId, 'con config:', configName);
    
    // Destruir instancia previa si existe
    if (CKEDITOR.instances[elementId]) {
        console.log('Destruyendo instancia previa de', elementId);
        CKEDITOR.instances[elementId].destroy(true);
    }

    const baseConfigs = {
        default: {
            toolbar: 'full',
            height: 300,
            contentsCss: ['/static/css/vendors/ckeditor_styles.css'],
            removeButtons: 'TextField,Textarea,Select,Button,ImageButton,HiddenField,Radio,Checkbox,Templates,CreateDiv,Iframe,BidiRtl,BidiLtr,Language',
            removePlugins: 'exportpdf'  // Deshabilitar plugin problemático
        },
        comments: {
            toolbar: 'Custom',
            toolbar_Custom: [
                ['Bold', 'Italic', 'Underline', 'Strike'],
                ['NumberedList', 'BulletedList', 'Blockquote'],
                ['Link', 'Unlink'],
                ['RemoveFormat']
            ],
            height: 120,
            removePlugins: 'elementspath,exportpdf',  // Deshabilitar plugins innecesarios
            resize_enabled: false,
            contentsCss: ['/static/css/vendors/ckeditor_styles.css']
        }
    };

    let finalConfig = baseConfigs[configName] || baseConfigs['default'];

    // --- CONFIGURACIÓN DE TEMA ---
    finalConfig.skin = 'moono-lisa';

    // Cargar Font Awesome (solo una vez)
    const faStyleTagId = 'ckeditor-fontawesome-style';
    if (!document.getElementById(faStyleTagId)) {
        const link = document.createElement('link');
        link.id = faStyleTagId;
        link.rel = 'stylesheet';
        link.type = 'text/css';
        link.href = '/static/css/vendors/ckeditor_fontawesome.css';
        document.head.appendChild(link);
    }

    // Cargar estilos de accesibilidad (solo una vez)
    const accessibilityStyleTagId = 'ckeditor-accessibility-style';
    if (!document.getElementById(accessibilityStyleTagId)) {
        const link = document.createElement('link');
        link.id = accessibilityStyleTagId;
        link.rel = 'stylesheet';
        link.type = 'text/css';
        link.href = '/static/css/vendors/ckeditor_accessibility.css';
        document.head.appendChild(link);
    }

    // Detectar modo oscuro
    const isDarkMode = document.body.classList.contains('dark-mode');
    const chromeStyleTagId = 'ckeditor-chrome-style';
    let existingChromeStyleTag = document.getElementById(chromeStyleTagId);

    if (isDarkMode) {
        finalConfig.uiColor = '#1c1c1e';
        
        // Cargar estilos oscuros si no existen
        if (!existingChromeStyleTag) {
            const link = document.createElement('link');
            link.id = chromeStyleTagId;
            link.rel = 'stylesheet';
            link.type = 'text/css';
            link.href = '/static/css/vendors/ckeditor_chrome_styles.css';
            document.head.appendChild(link);
        }
    } else {
        finalConfig.uiColor = '#ffffff';
        
        // Remover estilos oscuros si existen
        if (existingChromeStyleTag) {
            existingChromeStyleTag.remove();
        }
    }

    // Crear instancia del editor
    const editor = CKEDITOR.replace(elementId, finalConfig);

    // Aplicar tema al contenido del editor cuando esté listo
    editor.on('instanceReady', function(event) {
        console.log('Editor listo:', elementId);
        const editorInstance = event.editor;
        const iframeBody = editorInstance.document.getBody();
        
        if (isDarkMode) {
            iframeBody.addClass('dark-mode-editor');
        } else {
            iframeBody.removeClass('dark-mode-editor');
        }
    });

    return editor;
}