"""RentSmart - Orçamento de locação da R.M Imóveis."""
import csv
from abc import ABC, abstractmethod

TAXA_CONTRATUAL = 2000.00
MAX_PARCELAS = 5
MESES_PROJECAO = 12


def moeda(valor):
    """Formata como R$ 1.234,56."""
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


# ----------------------------------------------------------------------
# Imóveis
# ----------------------------------------------------------------------
class Imovel(ABC):
    """Classe base: cada imóvel sabe montar os itens do seu aluguel."""

    NOME = ""

    def __init__(self):
        self.itens = []  # lista de (descrição, valor)

    @abstractmethod
    def montar_itens(self):
        """Preenche self.itens com aluguel-base e adicionais."""

    def subtotal(self):
        return sum(valor for _, valor in self.itens)

    def desconto(self):
        return 0.0  # por padrão não há desconto

    def aluguel_mensal(self):
        return round(self.subtotal() - self.desconto(), 2)

    def descricao_desconto(self):
        return ""


class ImovelResidencial(Imovel):
    """Regras comuns a casas e apartamentos."""

    ALUGUEL_BASE = 0.0
    ADICIONAL_2_QUARTOS = 0.0
    VAGA_GARAGEM = 300.00

    def __init__(self, quartos, garagem):
        super().__init__()
        self.quartos = quartos
        self.garagem = garagem
        self.montar_itens()

    def montar_itens(self):
        self.itens = [(f"Aluguel-base ({self.NOME}, 1 quarto)", self.ALUGUEL_BASE)]
        if self.quartos == 2:
            self.itens.append(("Adicional de 2º quarto", self.ADICIONAL_2_QUARTOS))
        if self.garagem:
            self.itens.append(("Vaga de garagem", self.VAGA_GARAGEM))


class Apartamento(ImovelResidencial):
    NOME = "Apartamento"
    ALUGUEL_BASE = 700.00
    ADICIONAL_2_QUARTOS = 200.00
    DESCONTO_SEM_CRIANCAS = 0.05

    def __init__(self, quartos, garagem, tem_criancas):
        self.tem_criancas = tem_criancas
        super().__init__(quartos, garagem)

    def desconto(self):
        if not self.tem_criancas:
            return round(self.subtotal() * self.DESCONTO_SEM_CRIANCAS, 2)
        return 0.0

    def descricao_desconto(self):
        return "Desconto de 5% (cliente sem crianças)" if not self.tem_criancas else ""


class Casa(ImovelResidencial):
    NOME = "Casa"
    ALUGUEL_BASE = 900.00
    ADICIONAL_2_QUARTOS = 250.00


class Estudio(Imovel):
    NOME = "Estúdio"
    ALUGUEL_BASE = 1200.00
    PACOTE_INICIAL = 250.00  # 2 vagas
    VAGAS_PACOTE = 2
    VAGA_ADICIONAL = 60.00

    def __init__(self, vagas):
        super().__init__()
        self.vagas = vagas  # 0 (sem estacionamento) ou >= 2
        self.montar_itens()

    def montar_itens(self):
        self.itens = [("Aluguel-base (Estúdio)", self.ALUGUEL_BASE)]
        if self.vagas >= self.VAGAS_PACOTE:
            self.itens.append((f"Pacote inicial de {self.VAGAS_PACOTE} vagas", self.PACOTE_INICIAL))
            extras = self.vagas - self.VAGAS_PACOTE
            if extras > 0:
                self.itens.append((f"{extras} vaga(s) adicional(is) x {moeda(self.VAGA_ADICIONAL)}",
                                   extras * self.VAGA_ADICIONAL))


# ----------------------------------------------------------------------
# Orçamento
# ----------------------------------------------------------------------
class Orcamento:
    """Une imóvel + taxa contratual + parcelamento e gera resumo e CSV."""

    def __init__(self, imovel, parcelas, taxa=TAXA_CONTRATUAL):
        self.imovel = imovel
        self.parcelas = parcelas
        self.taxa = taxa

    def valores_parcelas(self):
        """Divide a taxa; a última parcela absorve a diferença de centavos."""
        base = round(self.taxa / self.parcelas, 2)
        valores = [base] * self.parcelas
        valores[-1] = round(self.taxa - base * (self.parcelas - 1), 2)
        return valores

    def exibir_resumo(self):
        print("\n" + "=" * 52)
        print(f"  ORÇAMENTO RENTSMART - {self.imovel.NOME.upper()}")
        print("=" * 52)
        print("Composição do aluguel mensal:")
        for descricao, valor in self.imovel.itens:
            print(f"  {descricao:<38}{moeda(valor):>12}")
        print(f"  {'Subtotal':<38}{moeda(self.imovel.subtotal()):>12}")
        if self.imovel.desconto() > 0:
            print(f"  {self.imovel.descricao_desconto():<38}"
                  f"{'- ' + moeda(self.imovel.desconto()):>12}")
        print(f"  {'ALUGUEL MENSAL':<38}{moeda(self.imovel.aluguel_mensal()):>12}")
        print("-" * 52)
        print("Taxa contratual (cobrada à parte do aluguel):")
        print(f"  Valor total: {moeda(self.taxa)}")
        parcelas = self.valores_parcelas()
        print(f"  Parcelamento: {self.parcelas}x de {moeda(parcelas[0])}")
        print("=" * 52)

    def gerar_projecao(self):
        """Retorna uma linha por mês, com aluguel, parcela da taxa e total."""
        parcelas = self.valores_parcelas()
        aluguel = self.imovel.aluguel_mensal()
        linhas = []
        for mes in range(1, MESES_PROJECAO + 1):
            parcela = parcelas[mes - 1] if mes <= self.parcelas else 0.0
            linhas.append({
                "Mês": mes,
                "Aluguel": aluguel,
                "Parcela da taxa": parcela,
                "Total do mês": round(aluguel + parcela, 2),
            })
        return linhas

    def exportar_csv(self, caminho="projecao_12_meses.csv"):
        linhas = self.gerar_projecao()
        with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
            escritor = csv.writer(arquivo, delimiter=";")
            escritor.writerow(["Mês", "Aluguel", "Parcela da taxa", "Total do mês"])
            for l in linhas:
                escritor.writerow([
                    l["Mês"],
                    f"{l['Aluguel']:.2f}".replace(".", ","),
                    f"{l['Parcela da taxa']:.2f}".replace(".", ","),
                    f"{l['Total do mês']:.2f}".replace(".", ","),
                ])
            total_ano = sum(l["Total do mês"] for l in linhas)
            escritor.writerow(["Total 12 meses", "", "", f"{total_ano:.2f}".replace(".", ",")])
        return caminho


# ----------------------------------------------------------------------
# Entrada de dados com validação
# ----------------------------------------------------------------------
def ler_inteiro(mensagem, minimo, maximo):
    while True:
        try:
            valor = int(input(mensagem))
            if minimo <= valor <= maximo:
                return valor
            print(f"  Digite um número entre {minimo} e {maximo}.")
        except ValueError:
            print("  Entrada inválida. Digite um número inteiro.")


def ler_sim_nao(mensagem):
    while True:
        resposta = input(mensagem + " (s/n): ").strip().lower()
        if resposta in ("s", "sim"):
            return True
        if resposta in ("n", "nao", "não"):
            return False
        print("  Responda com 's' ou 'n'.")


def coletar_imovel():
    print("Tipo de imóvel:\n  1 - Apartamento\n  2 - Casa\n  3 - Estúdio")
    tipo = ler_inteiro("Escolha: ", 1, 3)

    if tipo == 3:
        if ler_sim_nao("Deseja estacionamento?"):
            vagas = ler_inteiro("Total de vagas (mínimo 2, pacote inicial): ", 2, 20)
        else:
            vagas = 0
        return Estudio(vagas)

    quartos = ler_inteiro("Número de quartos (1 ou 2): ", 1, 2)
    garagem = ler_sim_nao("Deseja vaga de garagem?")
    if tipo == 1:
        tem_criancas = ler_sim_nao("Possui crianças?")
        return Apartamento(quartos, garagem, tem_criancas)
    return Casa(quartos, garagem)


def main():
    print("=== RentSmart - R.M Imóveis ===\n")
    imovel = coletar_imovel()
    parcelas = ler_inteiro(f"Parcelas da taxa contratual (1 a {MAX_PARCELAS}): ", 1, MAX_PARCELAS)

    orcamento = Orcamento(imovel, parcelas)
    orcamento.exibir_resumo()
    caminho = orcamento.exportar_csv()
    print(f"\nProjeção de 12 meses salva em: {caminho}")


if __name__ == "__main__":
    main()