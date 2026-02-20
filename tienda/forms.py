from django import forms
from .models import Labor, Tarea, Lote, Trabajador

class LaborForm(forms.ModelForm):
    class Meta:
        model = Labor
        fields = ['trabajador', 'tarea', 'finca', 'lote', 'cantidad', 'observaciones']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['lote'].queryset = Lote.objects.none()
        self.fields['trabajador'].queryset = Trabajador.objects.none()
        print("1")
        if 'finca' in self.data:
            print("2")
            try:
                print("3")
                finca_id = int(self.data.get('finca'))
                self.fields['lote'].queryset = Lote.objects.filter(finca_id=finca_id)
                self.fields['trabajador'].queryset = Trabajador.objects.filter(finca_id=finca_id).order_by('nombre_completo')
                print("Trabajadores cargados:", self.fields['trabajador'].queryset)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.finca:
            print("4")
            self.fields['lote'].queryset = Lote.objects.filter(finca=self.instance.finca)
            self.fields['trabajador'].queryset = self.instance.finca.trabajador_set.order_by('nombre_completo')
            print("Trabajadores cargados:", self.fields['trabajador'].queryset)

class TareaForm(forms.ModelForm):
    class Meta:
        model = Tarea
        fields = ['nombre', 'forma_medicion', 'valor_unitario']
