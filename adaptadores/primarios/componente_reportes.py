import streamlit as st


def renderizar_descargas_pdf(ciudad_sel, r):
    st.divider()
    st.markdown("### Descargar Reportes PDF")

    try:
        from adaptadores.secundarios.reportes.generador_pdf import generar_pdf_diagnostico, generar_pdf_estadistico

        datos_actuales = {
            'temperatura': r.datos.actual.temperatura,
            'humedad': r.datos.actual.humedad,
            'precipitacion': r.datos.actual.precipitacion,
        }
        pdf_diag = generar_pdf_diagnostico(
            ciudad_sel, datos_actuales,
            r.recomendacion_ia,
            st.session_state.chat_historial
        )
        st.download_button(
            label="Reporte de Diagnostico",
            data=pdf_diag,
            file_name=f"diagnostico_{ciudad_sel.replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="btn_descarga_diagnostico"
        )

        pronostico_lista = [
            {"fecha": d.fecha, "temperatura_max": d.temperatura_max,
             "temperatura_min": d.temperatura_min, "precipitacion": d.precipitacion,
             "humedad": d.humedad}
            for d in r.datos.pronostico
        ]
        alertas = [
            f"{c['etiqueta']}: {c['fecha']}" for c in r.clasificacion_dias
            if c['etiqueta'] == 'Riesgoso'
        ]
        pdf_est = generar_pdf_estadistico(
            ciudad_sel, pronostico_lista,
            r.estadisticas or {}, alertas
        )
        st.download_button(
            label="Reporte Estadistico",
            data=pdf_est,
            file_name=f"estadistico_{ciudad_sel.replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="btn_descarga_estadistico"
        )
    except ImportError:
        st.warning("Instala fpdf2 para habilitar la descarga de PDFs: pip install fpdf2")
    except Exception as e:
        st.error(f"Error al generar PDF: {e}")
