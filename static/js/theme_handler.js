// static/js/theme_handler.js - Versión corregida sin bucles

function applyThemeToCKEditorInstances(isDarkMode) {
    // NO aplicar clase al body aquí - eso lo hace el script principal
    
    // Esperar a que CKEditor esté listo
    if (!window.CKEDITOR_5_INSTANCES || Object.keys(window.CKEDITOR_5_INSTANCES).length === 0) {
        console.log('⏳ CKEditor aún no está listo, esperando...');
        return; // No reintentar automáticamente para evitar bucles
    }

    console.log('🎨 Aplicando tema a CKEditor:', isDarkMode ? 'oscuro' : 'claro');

    // Aplicar a todas las instancias de CKEditor
    Object.values(window.CKEDITOR_5_INSTANCES).forEach(editorInstance => {
        try {
            // Aplicar al área de edición directamente
            const editableElement = editorInstance.ui.view.editable.element;
            if (editableElement) {
                if (isDarkMode) {
                    editableElement.style.backgroundColor = '#1c1c1e';
                    editableElement.style.color = '#eaeaea';
                } else {
                    editableElement.style.backgroundColor = '#ffffff';
                    editableElement.style.color = '#222222';
                }
            }
        } catch (error) {
            console.error('Error aplicando tema a instancia de CKEditor:', error);
        }
    });

    console.log('✅ Tema aplicado a', Object.keys(window.CKEDITOR_5_INSTANCES).length, 'instancias');
}

document.addEventListener('DOMContentLoaded', function() {
    const themeSwitcher = document.querySelector('.theme-switch');
    
    // Aplicar tema inicial al cargar la página
    const isInitiallyDark = document.body.classList.contains('dark-mode');
    
    // Esperar un poco para asegurar que CKEditor esté completamente inicializado
    setTimeout(() => {
        applyThemeToCKEditorInstances(isInitiallyDark);
    }, 500);

    // Aplicar tema al hacer clic en el botón de cambio de tema
    if (themeSwitcher) {
        themeSwitcher.addEventListener('click', function() {
            // Dar tiempo al script principal para cambiar la clase del body
            setTimeout(() => {
                const isNowDark = document.body.classList.contains('dark-mode');
                applyThemeToCKEditorInstances(isNowDark);
            }, 100);
        });
    }
});