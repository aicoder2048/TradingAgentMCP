from symbols import SYMBOLS
from rich.table import Table
from rich import box
from ai_agent import DivinationAgent, SupportedModels

class HandTechnique:
    def __init__(self):
        self.ai_agent = DivinationAgent()

    @staticmethod
    def predict(num1, num2, num3, question=None, model_type=SupportedModels.OPENAI_GPT4O):
        symbols = HandTechnique.__generate_prediction(num1, num2, num3)
        table = HandTechnique.__format_prediction(symbols)

        interpretation = None
        if question:
            ai_agent = DivinationAgent(model_type)
            interpretation = ai_agent.interpret_prediction(symbols, question)

        return table, interpretation

    @staticmethod
    async def predict_async(num1, num2, num3, question=None, model_type=SupportedModels.OPENAI_GPT4O):
        """异步版本的预测方法，用于Web界面"""
        symbols = HandTechnique.__generate_prediction(num1, num2, num3)
        table = HandTechnique.__format_prediction(symbols)

        interpretation = None
        if question:
            ai_agent = DivinationAgent(model_type)
            interpretation = await ai_agent.interpret_prediction_async(symbols, question)

        return table, interpretation

    @staticmethod
    def __calculate_symbol(start_position, steps):
        # For numbers > 9, we use modulo 9 to map to 1-9 range
        # If steps % 9 == 0, we use 9 instead of 0
        normalized_steps = steps % 9
        if normalized_steps == 0:
            normalized_steps = 9
        end_position = (start_position + normalized_steps - 1) % 9
        return SYMBOLS[end_position]

    @staticmethod
    def __generate_prediction(num1, num2, num3):
        first_symbol = HandTechnique.__calculate_symbol(0, num1)
        second_symbol = HandTechnique.__calculate_symbol((num1 - 1) % 9, num2)
        third_symbol = HandTechnique.__calculate_symbol((num1 + num2 - 2) % 9, num3)
        return [first_symbol, second_symbol, third_symbol]

    @staticmethod
    def __format_prediction(symbols):
        table = Table(title="小六壬三传占卜", show_header=True, box=box.SIMPLE)
        table.add_column("初传（前期）", style="cyan", justify="center")
        table.add_column("关系", style="red", justify="center")
        table.add_column("中传（中期）", style="green", justify="center")
        table.add_column("关系", style="red", justify="center")
        table.add_column("末传（后期）", style="magenta", justify="center")

        # 添加符号名称
        table.add_row(
            f"【{symbols[0].name}】", "",
            f"【{symbols[1].name}】", "",
            f"【{symbols[2].name}】"
        )

        # 添加五行属性
        table.add_row(
            f"（{symbols[0].element.name}）", "",
            f"（{symbols[1].element.name}）", "",
            f"（{symbols[2].element.name}）"
        )

        # 添加生克关系
        relations = HandTechnique.__get_relations(symbols)

        table.add_row(
            "", f"[bold red]{relations[0]}→[/bold red]",
            "", f"[bold red]{relations[1]}→[/bold red]",
            ""
        )

        return table

    @staticmethod
    def __is_generating(element1, element2):
        return element1.generates == element2.name

    @staticmethod
    def __is_overcoming(element1, element2):
        return element1.overcomes == element2.name

    @staticmethod
    def __get_relations(symbols):
        relations = []
        for i in range(2):
            if HandTechnique.__is_generating(symbols[i].element, symbols[i+1].element):
                relation = "生"
            elif HandTechnique.__is_overcoming(symbols[i].element, symbols[i+1].element):
                relation = "克"
            else:
                relation = "无"
            relations.append(relation)
        return relations
