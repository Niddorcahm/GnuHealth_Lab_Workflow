# Guía de Contribución - health_lab_workflow

¡Gracias por tu interés en contribuir a health_lab_workflow! Esta guía te ayudará a contribuir de manera efectiva.

## 🚀 Cómo contribuir

### 1. Reportar bugs

Si encuentras un bug:

1. **Verifica** que no haya sido reportado en [Issues](https://github.com/tu-usuario/health_lab_workflow/issues)
2. **Crea un nuevo issue** incluyendo:
   - Descripción clara del problema
   - Pasos para reproducirlo
   - Comportamiento esperado vs actual
   - Versiones (GNUHealth, Tryton, Python)
   - Logs de error si aplica

### 2. Sugerir mejoras

Para sugerir nuevas características:

1. **Abre un issue** con la etiqueta "enhancement"
2. **Describe claramente** la funcionalidad
3. **Explica por qué** sería útil
4. **Incluye ejemplos** si es posible

### 3. Contribuir código

#### Preparación

1. **Fork** el repositorio
2. **Clona** tu fork:
   ```bash
   git clone https://github.com/tu-usuario/health_lab_workflow.git
   cd health_lab_workflow
   ```
3. **Crea una rama** para tu característica:
   ```bash
   git checkout -b feature/nombre-descriptivo
   ```

#### Estándares de código

- **Python**: Sigue PEP 8
- **Indentación**: 4 espacios
- **Líneas**: Máximo 79 caracteres
- **Docstrings**: Para todas las clases y métodos públicos
- **Nombres**: 
  - Clases: `CamelCase`
  - Funciones/métodos: `snake_case`
  - Constantes: `UPPER_CASE`

#### Ejemplo de código bien formateado:

```python
class GnuHealthLabWorkflowSample(ModelSQL, ModelView):
    """
    Lab Workflow Sample
    
    Manages the sample workflow from reception to completion.
    """
    __name__ = 'gnuhealth.lab.workflow.sample'
    
    def get_sample_info(self, name):
        """
        Get sample information based on field name
        
        :param name: Field name to retrieve
        :return: Field value or None
        """
        if self.workflow_sample:
            if name == 'name':
                return self.workflow_sample.name
        return None
```

#### Commits

- **Usa mensajes descriptivos** con prefijos:
  ```bash
  git commit -m "feat: Add new sample type for bone marrow"
  git commit -m "fix: Correct validation for PCR date fields"
  git commit -m "docs: Update README with new installation steps"
  ```

- **Prefijos válidos**:
  - `feat:` Nueva característica
  - `fix:` Corrección de bug
  - `docs:` Documentación
  - `style:` Formato (no afecta código)
  - `refactor:` Refactorización
  - `test:` Agregar tests
  - `chore:` Mantenimiento

#### Pull Request

1. **Push** tu rama:
   ```bash
   git push origin feature/nombre-descriptivo
   ```

2. **Abre un Pull Request** con:
   - Título descriptivo
   - Descripción de cambios
   - Referencias a issues relacionados (#123)
   - Screenshots si hay cambios visuales

3. **Asegúrate** de que:
   - El código sigue los estándares
   - No hay conflictos con main
   - Los tests pasan (si aplica)

### 4. Documentación

Ayuda mejorando la documentación:

- **Corrige** errores tipográficos
- **Mejora** ejemplos
- **Agrega** casos de uso
- **Traduce** a otros idiomas

### 5. Testing

Si agregas nueva funcionalidad, incluye tests:

```python
def test_sample_creation():
    """Test sample creation with all required fields"""
    sample = create_sample(
        name='TEST001',
        sample_type='blood',
        state='pending'
    )
    assert sample.name == 'TEST001'
    assert sample.sample_type == 'blood'
```

## 🛠️ Desarrollo local

### Configuración del entorno

```bash
# Instalar en entorno de desarrollo Tryton
cd /usr/local/lib/python3.x/dist-packages/trytond/modules/
git clone https://github.com/tu-usuario/health_lab_workflow.git

# Actualizar módulos
trytond-admin -d <database> --update-modules-list
trytond-admin -d <database> -i health_lab_workflow
```

### Estructura de desarrollo

```python
# Para agregar nuevos tipos de muestra
SAMPLE_TYPES = [
    ('blood', 'Blood'),
    ('new_type', 'New Sample Type'),  # Agregar aquí
    # ...
]

# Para agregar nuevos estudios
study_type = fields.Selection([
    ('existing_study', 'Existing Study'),
    ('new_study', 'New Study Type'),  # Agregar aquí
    # ...
])
```

### Testing local

```bash
# Actualizar módulo después de cambios
trytond-admin -d <database> -u health_lab_workflow

# Reiniciar servidor
sudo systemctl restart tryton

# Verificar logs
tail -f /var/log/tryton/tryton.log
```

## 📋 Checklist antes del PR

- [ ] El código sigue los estándares de Python/Tryton
- [ ] Todos los archivos XML son válidos
- [ ] Los nuevos campos tienen documentación
- [ ] Se agregaron validaciones donde corresponde
- [ ] No hay conflictos con la rama main
- [ ] El commit message es descriptivo
- [ ] Se probó en entorno local

## 🔍 Revisión de código

### Criterios de revisión

- **Funcionalidad**: ¿El código hace lo que debería?
- **Legibilidad**: ¿Es fácil de entender?
- **Mantenibilidad**: ¿Será fácil de modificar en el futuro?
- **Compatibilidad**: ¿Es compatible con GNUHealth 4.4.1/Tryton 6.0?
- **Documentación**: ¿Está bien documentado?

### Proceso de revisión

1. **Revisión automática**: GitHub Actions (si está configurado)
2. **Revisión manual**: Por maintainers del proyecto
3. **Feedback**: Se proporcionan comentarios constructivos
4. **Aprobación**: Una vez que cumple todos los criterios

## 💬 Comunicación

### Canales de comunicación

- **Issues**: Para reportes de bugs y solicitudes de características
- **Pull Requests**: Para revisión de código
- **Discussions**: Para preguntas generales y discusiones

### Código de conducta

- **Sé respetuoso** y profesional
- **Acepta críticas** constructivas
- **Enfócate** en lo mejor para la comunidad
- **Muestra empatía** hacia otros contribuyentes

## 🏆 Reconocimiento

Todos los contribuyentes serán agregados al archivo CONTRIBUTORS.md con sus respectivas contribuciones.

## ❓ Preguntas

Si tienes dudas:

1. **Revisa** la documentación existente
2. **Busca** en issues cerrados
3. **Abre un issue** con la etiqueta "question"

¡Gracias por contribuir a health_lab_workflow! 🚀