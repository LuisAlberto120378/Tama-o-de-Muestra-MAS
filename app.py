import math
from io import BytesIO
from datetime import date
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

st.set_page_config(page_title="CalcuMuestra Yarlequé", page_icon="📊", layout="centered")
st.markdown("""
<style>
.block-container{max-width:1000px;padding-top:1.8rem}
h1{font-size:2.2rem!important}
div[data-testid="stForm"]{border:1px solid #d9e2ec;padding:1.1rem;border-radius:12px}
.stButton button,.stDownloadButton button{min-height:2.8rem;font-size:1rem;font-weight:600}
div[data-testid="stMetric"]{border:1px solid #d9e2ec;padding:1rem;border-radius:10px}
</style>
""", unsafe_allow_html=True)

st.title("📊 CalcuMuestra Yarlequé")
st.caption("Calculadora de tamaño de muestra | Estadística e investigación")
st.info("Herramienta de apoyo académico. Verifica los supuestos y el diseño muestral antes de usar resultados en una investigación real.")

with st.form("muestra"):
    st.header("1. Identificación del estudio")
    a,b=st.columns(2)
    with a:
        unidad=st.text_input("Unidad de análisis","Pacientes atendidos")
        lugar=st.text_input("Lugar","Hospital")
    with b:
        periodo=st.text_input("Periodo",str(date.today().year))
        variable=st.text_input("Variable principal (opcional)","")
    poblacion_obj=st.text_area("Población objetivo","Pacientes atendidos en un establecimiento de salud",height=75)

    st.header("2. Tipo de variable y población")
    tipo=st.selectbox("Tipo de variable",["Categórica: proporción o porcentaje","Numérica: estimación de una media"])
    estado=st.radio("Tamaño de la población",["Conocida: ingresar N","Desconocida o muy grande"],horizontal=True)
    N=st.number_input("Tamaño de la población (N)",min_value=2,value=1200,step=1) if estado=="Conocida: ingresar N" else None

    st.header("3. Parámetros estadísticos")
    c,d=st.columns(2)
    with c:
        confianza=st.selectbox("Nivel de confianza (%)",[90,95,99],index=1)
        error_pct=st.number_input("Margen de error (%)",min_value=0.1,max_value=50.0,value=5.0,step=0.5)
    with d:
        if tipo.startswith("Categórica"):
            p_pct=st.number_input("Proporción esperada p (%)",min_value=1.0,max_value=99.0,value=50.0,step=1.0)
            sigma=None
        else:
            sigma=st.number_input("Desviación estándar (σ)",min_value=0.0001,value=10.0,step=0.5,help="El margen de error debe estar en las mismas unidades que σ.")
            p_pct=None
        no_resp=st.number_input("No respuesta esperada (%)",min_value=0.0,max_value=90.0,value=10.0,step=1.0)
    enviar=st.form_submit_button("Calcular tamaño de muestra",type="primary",use_container_width=True)

def calcular(confianza,error_pct,N,p_pct,sigma,no_resp):
    z={90:1.6448536269514722,95:1.959963984540054,99:2.5758293035489004}[confianza]
    e=error_pct/100 if p_pct is not None else error_pct
    if p_pct is not None:
        p=p_pct/100
        base=z*z*p*(1-p)
        formula_finita=r"n=\frac{NZ^2pq}{e^2(N-1)+Z^2pq}"
        formula_infinita=r"n=\frac{Z^2pq}{e^2}"
    else:
        base=z*z*sigma*sigma
        formula_finita=r"n=\frac{NZ^2\sigma^2}{e^2(N-1)+Z^2\sigma^2}"
        formula_infinita=r"n=\frac{Z^2\sigma^2}{e^2}"
    n0=base/(e*e)
    ncont=N*base/(e*e*(N-1)+base) if N is not None else n0
    n=math.ceil(ncont)
    nadj=math.ceil(n/(1-no_resp/100)) if no_resp else n
    return z,e,n0,ncont,n,nadj,formula_finita if N is not None else formula_infinita

def pdf_informe(datos):
    buff=BytesIO()
    doc=SimpleDocTemplate(buff,pagesize=A4,rightMargin=42,leftMargin=42,topMargin=42,bottomMargin=42)
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TituloCM",parent=styles["Title"],alignment=TA_CENTER,textColor=colors.HexColor("#174A70")))
    rows=[["Campo","Detalle"]]+[[str(k),str(v)] for k,v in datos.items()]
    table=Table(rows,colWidths=[175,300],repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#174A70")),("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#CBD5E1")),
        ("VALIGN",(0,0),(-1,-1),"TOP"),("BACKGROUND",(0,1),(0,-1),colors.HexColor("#EFF4F8")),
        ("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),
        ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)
    ]))
    story=[Paragraph("CalcuMuestra Yarlequé",styles["TituloCM"]),Paragraph("Informe de cálculo del tamaño de muestra",styles["Heading2"]),Spacer(1,12),table,Spacer(1,18),Paragraph("YARLEQUÉ | Estadístico Informático e Investigación",styles["Italic"])]
    doc.build(story)
    return buff.getvalue()

if enviar:
    z,e,n0,ncont,n,nadj,formula=calcular(confianza,error_pct,int(N) if N is not None else None,p_pct,sigma,no_resp)
    st.success("Cálculo completado")
    x,y=st.columns(2)
    x.metric("Tamaño de muestra requerido",n)
    y.metric("Cantidad recomendada a convocar",nadj)
    st.subheader("Fórmula aplicada")
    st.latex(formula)
    st.write(f"Valor crítico Z: **{z:.6f}**")
    st.write(f"Tamaño calculado antes del redondeo: **{ncont:.6f}**")
    if p_pct is not None:
        st.write(f"Proporción p: **{p_pct:.2f}%** | q: **{100-p_pct:.2f}%**")
    else:
        st.write(f"Desviación estándar σ: **{sigma:g}**")
    st.caption("El ajuste por no respuesta se calcula como techo[n / (1 − tasa de no respuesta)].")
    datos={
        "Unidad de análisis":unidad,"Población objetivo":poblacion_obj,"Lugar":lugar,"Periodo":periodo,
        "Variable principal":variable or "No especificada","Tipo de variable":tipo,"Población":estado,
        "Tamaño N":int(N) if N is not None else "Desconocido / muy grande",
        "Nivel de confianza":f"{confianza}%","Valor crítico Z":f"{z:.6f}",
        "Margen de error":f"{error_pct}% " + ("(proporción)" if p_pct is not None else "(unidades de la variable)"),
        "Proporción p":f"{p_pct}%" if p_pct is not None else "No aplica",
        "Desviación estándar σ":sigma if sigma is not None else "No aplica",
        "Fórmula":formula,"Tamaño antes del redondeo":f"{ncont:.6f}","Tamaño requerido":n,
        "No respuesta esperada":f"{no_resp}%","Cantidad a convocar":nadj
    }
    st.download_button("📄 Descargar informe PDF",pdf_informe(datos),"Informe_CalcuMuestra_Yarleque.pdf","application/pdf",use_container_width=True)

with st.expander("Acerca de CalcuMuestra Yarlequé"):
    st.write("Autor: Dr. Calderón Yalrequé Luis Alberto")
    st.write("Especialidad: Estadístico Informático e Investigación")
    st.write("Herramienta de apoyo académico para estadística e investigación.")
