#!/usr/bin/env python3
"""Convert scanned single pages/book spreads into page-addressable Markdown.

Requires pdftoppm, pdfinfo, Tesseract (rus+eng), and Python Pillow.
OCR intermediates are cached under build/manuals; input PDFs are read-only.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import os
from pathlib import Path
import re
import subprocess
from PIL import Image


def convert(pdf, output, cache, tesseract, jobs, dpi, corrections):
    info = subprocess.check_output(['pdfinfo', str(pdf)], text=True)
    pages = int(re.search(r'^Pages:\s+(\d+)', info, re.M)[1])
    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    folder = cache / pdf.stem
    folder.mkdir(parents=True, exist_ok=True)
    stamp = f'{digest}\n{dpi}\nrus+eng psm3 split-spreads v1\n'
    stamp_file = folder / 'source.txt'
    if stamp_file.exists() and stamp_file.read_text() != stamp:
        raise ValueError(f'{folder}: cache belongs to different input/settings')
    stamp_file.write_text(stamp)
    env = dict(os.environ, OMP_THREAD_LIMIT='1')

    def page(number):
        files = sorted(folder.glob(f'{number:03d}-*.txt'))
        done = folder / f'{number:03d}.done'
        if done.exists():
            return number, [(p.stem.split('-')[1], p.read_text()) for p in files]
        prefix = folder / f'{number:03d}'
        subprocess.run(['pdftoppm', '-f', str(number), '-l', str(number),
                        '-r', str(dpi), '-gray', '-png', '-singlefile',
                        str(pdf), str(prefix)], check=True, capture_output=True)
        with Image.open(prefix.with_suffix('.png')) as scan:
            width, height = scan.size
            parts = [('left', (0, 0, width // 2, height)),
                     ('right', (width // 2, 0, width, height))] if width > height * 1.12 else [
                         ('page', (0, 0, width, height))]
            results = []
            for side, box in parts:
                picture = folder / f'{number:03d}-{side}.png'
                scan.crop(box).save(picture)
                result = subprocess.run([tesseract, str(picture), 'stdout', '-l', 'rus+eng',
                                         '--psm', '3', '-c', 'preserve_interword_spaces=1'],
                                        check=True, capture_output=True, text=True, env=env)
                text = result.stdout.replace('\x0c', '').strip()
                (folder / f'{number:03d}-{side}.txt').write_text(text + '\n')
                results.append((side, text))
        done.touch()
        return number, results

    results = {}
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = [pool.submit(page, n) for n in range(1, pages + 1)]
        for future in as_completed(futures):
            number, parts = future.result()
            results[number] = parts
            print(f'{pdf.name}: PDF page {number}/{pages}', flush=True)
    title = ('Система ПУЛЬТ-78. Руководство к пользованию' if 'User' in pdf.stem else
             'Система ПУЛЬТ-78. Общая структура и рекомендации по обслуживанию')
    relative = os.path.relpath(pdf, output.parent)
    lines = [f'# {title}', '', f'Источник: [{pdf.name}]({relative}), ВЦ АН СССР, 1978.', '',
             '**Полный OCR-текст скана, не вычитанная транскрипция.** '
             'Все PDF-страницы включены; развороты читаются слева направо. '
             'Номера PDF-страниц отличаются от печатной нумерации. '
             'Машинные коды, латинские/кириллические буквы, формулы, таблицы и '
             'специальные символы могут содержать ошибки распознавания. '
             'Пустые/графические страницы также отмечены. '
             'Блоки text сохраняют строки и отступы OCR. '
             'Вручную сверенные части отмечены отдельно.', '',
             f'SHA-256 исходного PDF: `{digest}`.', '',
             'Воспроизведение: `python3 tools/pdfmanual.py` (Tesseract rus+eng, '
             'Poppler, Pillow). Промежуточные результаты: `build/manuals/`.', '',
             '## Указатель PDF-страниц', '']
    lines += [f'- [PDF {n}](#pdf-{n:03d})' for n in range(1, pages + 1)]
    leaves = 0
    for n in range(1, pages + 1):
        lines += ['', f'<a id="pdf-{n:03d}"></a>', '', f'## PDF {n}', '',
                  f'[Скан PDF-страницы {n}]({relative}#page={n})', '']
        for side, content in results[n]:
            leaves += 1
            label = {'left': 'Левая сторона', 'right': 'Правая сторона', 'page': 'Страница'}[side]
            # Both supplied books start printed pp. 2–3 on PDF spread 3.
            # Do not apply this book-specific numbering to unrelated PDFs.
            if pdf.stem in ('PULT', 'PULT-User') and side != 'page' and n >= 3:
                label += f' — печатная страница {2 * n - 4 + (side == "right")}'
            lines += [f'### {label}', '']
            correction = corrections / f'{pdf.stem}-{n:03d}-{side}.md'
            if correction.exists():
                lines += ['_Эта сторона сверена со сканом вручную._', '',
                          correction.read_text().strip(), '']
            elif content.strip():
                fence = '`' * max(3, max((len(s) + 1 for s in re.findall(r'`+', content)), default=3))
                lines += [f'{fence}text', content.rstrip(), fence, '']
            else:
                lines += ['_OCR не обнаружил текста; см. скан._', '']
    output.write_text('\n'.join(lines).rstrip() + '\n')
    print(f'Wrote {output}: {pages} PDF pages, {leaves} page sides', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf', type=Path, nargs='*', default=[Path('PULT.pdf'), Path('PULT-User.pdf')])
    parser.add_argument('--output-dir', type=Path, default=Path('doc'))
    parser.add_argument('--cache', type=Path, default=Path('build/manuals'))
    parser.add_argument('--tesseract', default='tesseract')
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--dpi', type=int, default=200)
    parser.add_argument('--corrections', type=Path, default=Path('doc/manual-corrections'))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for pdf in args.pdf:
        convert(pdf, args.output_dir / (pdf.stem + '.md'), args.cache,
                args.tesseract, args.jobs, args.dpi, args.corrections)


if __name__ == '__main__':
    main()
