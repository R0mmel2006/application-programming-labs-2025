import os
import argparse
from typing import List
import pandas as pd

from data_processor import DataFrameProcessor
from visualizer import HistogramPlotter


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Анализ яркости изображений.")
    parser.add_argument(
        "--bins",
        type=str,
        default="50,100,150,200",
        help="Границы диапазонов через запятую (напр. 80,160,240)"
    )
    return parser.parse_args()


def parse_bins_string(bins_str: str) -> List[int]:
    try:
        bins = sorted(list(set(int(x.strip()) for x in bins_str.split(',') if x.strip().isdigit())))
        valid_bins = [b for b in bins if 0 <= b < 255]
        if not valid_bins:
            print("Предупреждение: введены некорректные диапазоны. Используются стандартные.")
            return [50, 100, 150, 200]
        return valid_bins
    except Exception:
        print("Ошибка парсинга диапазонов. Используются стандартные.")
        return [50, 100, 150, 200]


def find_or_create_annotation_file(start_path: str) -> str:
    """
    Ищет annotation.csv. Если не найден — создаёт его, сканируя папку на изображения.
    """
    filename = "annotation.csv"
    full_path = os.path.join(start_path, filename)

    if os.path.exists(full_path):
        return full_path

    SUPPORTED_EXTS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}
    image_files = []

    for f in os.listdir(start_path):
        if os.path.isfile(os.path.join(start_path, f)):
            _, ext = os.path.splitext(f)
            if ext.lower() in SUPPORTED_EXTS:
                image_files.append(f)

    if not image_files:
        print("❌ Не найдено изображений в текущей папке для автоматического создания annotation.csv!")
        return ""

    abs_paths = [os.path.abspath(os.path.join(start_path, f)) for f in image_files]
    rel_paths = [f for f in image_files]

    df = pd.DataFrame({
        "Абсолютный путь": abs_paths,
        "Относительный путь": rel_paths
    })

    df.to_csv(full_path, index=False, encoding='utf-8-sig')
    print(f"✅ Файл annotation.csv успешно создан с {len(image_files)} изображениями.")
    return full_path


def main() -> None:
    args = parse_arguments()
    user_bins = parse_bins_string(args.bins)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_plot = os.path.join(current_dir, "brightness_histogram.png")
    output_csv = os.path.join(current_dir, "analyzed_data.csv")

    input_csv = find_or_create_annotation_file(current_dir)
    if not input_csv:
        print("❌ Невозможно продолжить: нет изображений и нет annotation.csv.")
        return

    try:
        processor = DataFrameProcessor(input_csv)
        processor.rename_columns()

        print(f"Используемые границы диапазонов: {user_bins}")
        processor.add_brightness_ranges(user_bins)

        sorted_df = processor.sort_by_column('r_range')
        bin_order = processor.get_bin_order()

        plotter = HistogramPlotter(processor.df, bin_order)
        plotter.plot_rgb_histograms(output_plot, sorted_df)

        processor.save_csv(output_csv)
        print(f"✅ Готово! Результаты:")
        print(f"   - График: {output_plot}")
        print(f"   - CSV:    {output_csv}")

    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    main()