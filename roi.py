import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import base64
from io import BytesIO

# Configuração da página
st.set_page_config(
    page_title="Calculadora de ROI para Campanhas de KOL - Ledger",
    page_icon="💰",
    layout="wide"
)

# Funções auxiliares
def format_currency(value):
    return f"${value:,.2f}"

def format_number(value):
    return f"{value:,}"

def format_percent(value):
    return f"{value:.2f}%"

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Resultados', index=False)
        workbook = writer.book
        worksheet = writer.sheets['Resultados']
        
        # Formatar colunas
        money_fmt = workbook.add_format({'num_format': '$#,##0.00'})
        percent_fmt = workbook.add_format({'num_format': '0.00%'})
        
        # Aplicar formatação
        worksheet.set_column('E:E', 18, money_fmt)  # Receita
        worksheet.set_column('F:F', 18, money_fmt)  # Custo
        worksheet.set_column('G:G', 15, percent_fmt)  # ROI
    
    processed_data = output.getvalue()
    return processed_data

def download_link(df, filename, text):
    val = to_excel(df)
    b64 = base64.b64encode(val)
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{filename}">{text}</a>'

# Título e descrição
st.title("Calculadora de ROI para Campanhas de KOL - Ledger")
st.markdown("""
Esta calculadora permite estimar o ROI de campanhas com Key Opinion Leaders (KOLs) para produtos Ledger, 
considerando diferentes metodologias de cálculo e fatores de ajuste.
""")

# Sidebar para parâmetros gerais
st.sidebar.header("Parâmetros Gerais da Campanha")

budget = st.sidebar.number_input(
    "Orçamento Total (USD)",
    min_value=0,
    value=30000,
    step=1000,
    help="Orçamento total disponível para a campanha"
)

avg_order_value = st.sidebar.number_input(
    "Valor Médio do Pedido (USD)",
    min_value=0,
    value=400,
    step=50,
    help="Valor médio de cada compra realizada"
)

conversion_rate = st.sidebar.number_input(
    "Taxa de Conversão da Indústria (%)",
    min_value=0.0,
    max_value=100.0,
    value=4.0,
    step=0.1,
    help="Percentual médio de conversões no setor de criptomoedas"
) / 100  # Converter para decimal

calculation_method = st.sidebar.selectbox(
    "Método de Cálculo",
    options=["Direto (Alcance → Vendas)", "Com Engajamento (Alcance → Engajamento → Vendas)"],
    index=0,
    help="Escolha entre cálculo direto ou com engajamento como etapa intermediária"
)

use_adjustment = st.sidebar.checkbox(
    "Usar fatores de ajuste para ROI realista",
    value=True,
    help="Aplicar fatores para obter um ROI mais realista"
)

if use_adjustment:
    cost_factor = st.sidebar.number_input(
        "Fator de Custo Adicional",
        min_value=1.0,
        value=1.5,
        step=0.1,
        help="Multiplicador para custos adicionais (logística, gestão, etc.)"
    )
    
    attribution_factor = st.sidebar.number_input(
        "Fator de Atribuição (%)",
        min_value=0.0,
        max_value=100.0,
        value=60.0,
        step=5.0,
        help="Percentual de vendas atribuídas diretamente à campanha de KOL"
    ) / 100  # Converter para decimal
else:
    cost_factor = 1.0
    attribution_factor = 1.0

# Metodologia de cálculo
with st.expander("Metodologia de Cálculo", expanded=False):
    st.markdown("""
    ### Método Direto (Alcance → Vendas)
    Esta metodologia calcula as vendas esperadas diretamente a partir do alcance, multiplicando-o pela taxa de conversão da indústria.
    
    ```
    Expected Sales = Expected Reach × Taxa de Conversão
    ```
    
    ### Método com Engajamento (Alcance → Engajamento → Vendas)
    Esta metodologia inclui o engajamento como etapa intermediária no cálculo das vendas esperadas.
    
    ```
    Expected Sales = Expected Reach × Taxa de Engajamento × Taxa de Conversão
    ```
    
    ### Cálculo de ROI
    O ROI (Retorno sobre Investimento) é calculado pela fórmula:
    
    ```
    ROI (%) = ((Receita × Fator de Atribuição - Custo × Fator de Custo) / (Custo × Fator de Custo)) × 100
    ```
    """)

# Entrada de dados dos KOLs
st.header("Informações dos KOLs")

# Dados pré-preenchidos para os 4 KOLs iniciais
default_kols = [
    {
        "name": "Isabela Martin",
        "followers": 1000000,
        "reach_rate": 7.0,
        "engagement_rate": 7.0,
        "deliverables": "Reels",
        "cost": 10000,
        "size": "Macro",
        "target": "Newcomers & Investors"
    },
    {
        "name": "Lucas Williams",
        "followers": 800000,
        "reach_rate": 6.0,
        "engagement_rate": 6.0,
        "deliverables": "Reels",
        "cost": 7500,
        "size": "Mid",
        "target": "Newcomers & Investors"
    },
    {
        "name": "Gustavo Anderson",
        "followers": 300000,
        "reach_rate": 9.0,
        "engagement_rate": 9.0,
        "deliverables": "Reels + Stories",
        "cost": 7000,
        "size": "Micro",
        "target": "Newcomers"
    },
    {
        "name": "Manuela Dubois",
        "followers": 200000,
        "reach_rate": 10.0,
        "engagement_rate": 10.0,
        "deliverables": "Reels + Stories",
        "cost": 5500,
        "size": "Micro",
        "target": "Investors"
    }
]

# Inicializar o estado da sessão para KOLs se ainda não existir
if 'kols' not in st.session_state:
    st.session_state.kols = default_kols.copy()
    st.session_state.kol_count = len(default_kols)

# Função para adicionar um novo KOL
def add_kol():
    st.session_state.kols.append({
        "name": f"Novo KOL #{st.session_state.kol_count + 1}",
        "followers": 100000,
        "reach_rate": 5.0,
        "engagement_rate": 5.0,
        "deliverables": "Reels",
        "cost": 5000,
        "size": "Micro",
        "target": "Newcomers"
    })
    st.session_state.kol_count += 1

# Função para remover um KOL
def remove_kol(index):
    if len(st.session_state.kols) > 1:  # Sempre manter pelo menos um KOL
        st.session_state.kols.pop(index)
        st.session_state.kol_count -= 1

# Container para os KOLs
kol_cols = st.columns(2)
updated_kols = []

for i, kol in enumerate(st.session_state.kols):
    with st.container():
        st.subheader(f"KOL #{i+1}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input(
                "Nome do KOL",
                value=kol["name"],
                key=f"name-{i}"
            )
            
            followers = st.number_input(
                "Número de Seguidores",
                min_value=0,
                value=kol["followers"],
                step=10000,
                key=f"followers-{i}"
            )
            
            reach_rate = st.number_input(
                "Taxa de Alcance (%)",
                min_value=0.0,
                max_value=100.0,
                value=kol["reach_rate"],
                step=0.1,
                key=f"reach-{i}",
                help="Percentual dos seguidores alcançados"
            )
            
            engagement_rate = st.number_input(
                "Taxa de Engajamento (%)",
                min_value=0.0,
                max_value=100.0,
                value=kol["engagement_rate"],
                step=0.1,
                key=f"engagement-{i}",
                help="Percentual de alcance que gera engajamento"
            )
        
        with col2:
            deliverables = st.selectbox(
                "Tipo de Entrega",
                options=["Reels", "Stories", "Reels + Stories"],
                index=["Reels", "Stories", "Reels + Stories"].index(kol["deliverables"]),
                key=f"deliverables-{i}"
            )
            
            cost = st.number_input(
                "Custo (USD)",
                min_value=0,
                value=kol["cost"],
                step=500,
                key=f"cost-{i}",
                help="Valor total pago ao KOL"
            )
            
            size = st.selectbox(
                "Tamanho",
                options=["Macro", "Mid", "Micro"],
                index=["Macro", "Mid", "Micro"].index(kol["size"]),
                key=f"size-{i}"
            )
            
            target = st.selectbox(
                "Público-Alvo",
                options=["Newcomers", "Investors", "Newcomers & Investors"],
                index=["Newcomers", "Investors", "Newcomers & Investors"].index(kol["target"]),
                key=f"target-{i}"
            )
        
        # Botão para remover KOL (exceto o primeiro)
        if i > 0:
            if st.button(f"Remover KOL #{i+1}", key=f"remove-{i}"):
                remove_kol(i)
                st.experimental_rerun()
        
        st.markdown("---")
        
        # Atualizar dados do KOL
        updated_kols.append({
            "name": name,
            "followers": followers,
            "reach_rate": reach_rate,
            "engagement_rate": engagement_rate,
            "deliverables": deliverables,
            "cost": cost,
            "size": size,
            "target": target
        })

# Atualizar a lista de KOLs no estado da sessão
st.session_state.kols = updated_kols

# Botão para adicionar novo KOL
if st.button("+ Adicionar KOL", type="primary"):
    add_kol()
    st.experimental_rerun()

# Botão para calcular o ROI
calculate_button = st.button("Calcular ROI da Campanha", use_container_width=True)

# Realizar cálculos quando o botão for pressionado
if calculate_button:
    st.header("Resultados da Análise de ROI")
    
    # Preparar dados para cálculos
    results = []
    
    total_reach = 0
    total_sales = 0
    total_revenue = 0
    total_cost = 0
    
    for kol in st.session_state.kols:
        # Calcular alcance esperado
        expected_reach = int(kol["followers"] * (kol["reach_rate"] / 100))
        
        # Calcular vendas esperadas com base no método selecionado
        if calculation_method == "Direto (Alcance → Vendas)":
            expected_sales = int(expected_reach * conversion_rate)
        else:  # Com engajamento
            expected_sales = int(expected_reach * (kol["engagement_rate"] / 100) * conversion_rate)
        
        # Calcular receita e ROI
        revenue = expected_sales * avg_order_value
        adjusted_revenue = revenue * attribution_factor
        adjusted_cost = kol["cost"] * cost_factor
        
        roi = ((adjusted_revenue - adjusted_cost) / adjusted_cost) * 100
        
        # Adicionar aos totais
        total_reach += expected_reach
        total_sales += expected_sales
        total_revenue += adjusted_revenue
        total_cost += adjusted_cost
        
        # Adicionar aos resultados
        results.append({
            "KOL": kol["name"],
            "Tamanho": kol["size"],
            "Entregas": kol["deliverables"],
            "Alcance": expected_reach,
            "Vendas": expected_sales,
            "Receita": adjusted_revenue,
            "Custo": adjusted_cost,
            "ROI (%)": roi,
            "Público-Alvo": kol["target"]
        })
    
    # Calcular ROI médio
    total_roi = ((total_revenue - total_cost) / total_cost) * 100 if total_cost > 0 else 0
    
    # Exibir cards com os principais KPIs
    kpi_cols = st.columns(4)
    
    with kpi_cols[0]:
        st.metric("ROI Médio", format_percent(total_roi))
    
    with kpi_cols[1]:
        st.metric("Alcance Total", format_number(total_reach))
    
    with kpi_cols[2]:
        st.metric("Vendas Estimadas", format_number(total_sales))
    
    with kpi_cols[3]:
        st.metric("Receita Projetada", format_currency(total_revenue))
    
    # Criar DataFrame com os resultados
    df_results = pd.DataFrame(results)
    
    # Exibir tabela de resultados
    st.subheader("Detalhamento por KOL")
    
    # Formatação para exibição
    df_display = df_results.copy()
    df_display["Alcance"] = df_display["Alcance"].apply(format_number)
    df_display["Vendas"] = df_display["Vendas"].apply(format_number)
    df_display["Receita"] = df_display["Receita"].apply(format_currency)
    df_display["Custo"] = df_display["Custo"].apply(format_currency)
    df_display["ROI (%)"] = df_display["ROI (%)"].apply(format_percent)
    
    st.dataframe(df_display, use_container_width=True)
    
    # Gráficos
    st.subheader("Visualizações")
    
    chart_cols = st.columns(2)
    
    with chart_cols[0]:
        # Gráfico de ROI por KOL
        fig_roi = px.bar(
            df_results,
            x="KOL",
            y="ROI (%)",
            color="Tamanho",
            title="ROI por KOL",
            text_auto='.2f',
            color_discrete_map={"Macro": "#1F77B4", "Mid": "#FF7F0E", "Micro": "#2CA02C"}
        )
        fig_roi.update_layout(yaxis_title="ROI (%)")
        st.plotly_chart(fig_roi, use_container_width=True)
    
    with chart_cols[1]:
        # Gráfico de Custo vs. Receita
        fig_cost_rev = go.Figure()
        
        fig_cost_rev.add_trace(go.Bar(
            x=df_results["KOL"],
            y=df_results["Custo"],
            name="Custo",
            marker_color="#FF6B6B"
        ))
        
        fig_cost_rev.add_trace(go.Bar(
            x=df_results["KOL"],
            y=df_results["Receita"],
            name="Receita",
            marker_color="#4ECDC4"
        ))
        
        fig_cost_rev.update_layout(
            title="Custo vs. Receita por KOL",
            barmode="group",
            yaxis_title="USD"
        )
        
        st.plotly_chart(fig_cost_rev, use_container_width=True)
    
    # Gráfico de distribuição de alcance
    fig_reach = px.pie(
        df_results,
        values="Alcance",
        names="KOL",
        title="Distribuição de Alcance por KOL"
    )
    fig_reach.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_reach, use_container_width=True)
    
    # Resumo dos fatores de ajuste utilizados
    if use_adjustment:
        st.subheader("Fatores de Ajuste Aplicados")
        adj_cols = st.columns(2)
        
        with adj_cols[0]:
            st.metric("Fator de Custo Adicional", f"{cost_factor:.1f}x")
        
        with adj_cols[1]:
            st.metric("Fator de Atribuição", f"{attribution_factor*100:.0f}%")
        
        st.markdown("""
        **Nota sobre os ajustes:**
        - O Fator de Custo Adicional multiplica o custo nominal para considerar despesas extras (logística, gestão, etc.)
        - O Fator de Atribuição representa a porcentagem das vendas que podem ser diretamente atribuídas à campanha de KOL
        """)
    
    # Botão para exportar resultados
    st.subheader("Exportar Resultados")
    
    if not df_results.empty:
        excel_data = to_excel(df_results)
        st.download_button(
            label="📊 Baixar Resultados em Excel",
            data=excel_data,
            file_name="resultados_roi_kol_ledger.xlsx",
            mime="application/vnd.ms-excel",
            use_container_width=True
        )

# Rodapé com informações
st.markdown("---")
st.caption("Calculadora de ROI para Campanhas de KOL - Ledger | Developed for ROI KOL analysis")
