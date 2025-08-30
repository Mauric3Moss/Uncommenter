import re
import os
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class CommentRemover:
    def __init__(self):

        self.language_patterns = {
            'python': {
                'extensions': ['.py', '.pyw'],
                'single_line': ['#'],
                'multi_line': [('   ', '   '), ("   ", "   ")],
                'string_delimiters': ['"', "'", '   ', "   "]
            },
            'javascript': {
                'extensions': ['.js', '.jsx', '.mjs'],
                'single_line': ['//'],
                'multi_line': [('/*', '*/')],
                'string_delimiters': ['"', "'", '`']
            },
            'typescript': {
                'extensions': ['.ts', '.tsx'],
                'single_line': ['//'],
                'multi_line': [('/*', '*/')],
                'string_delimiters': ['"', "'", '`']
            },
            'java': {
                'extensions': ['.java'],
                'single_line': ['//'],
                'multi_line': [('/*', '*/')],
                'string_delimiters': ['"', "'"]
            },
            'c_cpp': {
                'extensions': ['.c', '.cpp', '.cc', '.cxx', '.h', '.hpp'],
                'single_line': ['//'],
                'multi_line': [('/*', '*/')],
                'string_delimiters': ['"', "'"]
            },
            'shell': {
                'extensions': ['.sh', '.bash', '.zsh', '.fish'],
                'single_line': ['#'],
                'multi_line': [],
                'string_delimiters': ['"', "'"]
            },
            'perl': {
                'extensions': ['.pl', '.pm', '.perl'],
                'single_line': ['#'],
                'multi_line': [('=pod', '=cut')],
                'string_delimiters': ['"', "'"]
            },
            'ruby': {
                'extensions': ['.rb', '.ruby'],
                'single_line': ['#'],
                'multi_line': [('=begin', '=end')],
                'string_delimiters': ['"', "'"]
            },
            'php': {
                'extensions': ['.php'],
                'single_line': ['#', '//'],
                'multi_line': [('/*', '*/')],
                'string_delimiters': ['"', "'"]
            },
            'css': {
                'extensions': ['.css', '.scss', '.sass', '.less'],
                'single_line': ['//'],
                'multi_line': [('/*', '*/')],
                'string_delimiters': ['"', "'"]
            },
            'html_xml': {
                'extensions': ['.html', '.htm', '.xml', '.xhtml'],
                'single_line': [],
                'multi_line': [('<!--', '-->')],
                'string_delimiters': ['"', "'"]
            },
            'sql': {
                'extensions': ['.sql'],
                'single_line': ['--'],
                'multi_line': [('/*', '*/')],
                'string_delimiters': ['"', "'"]
            },
            'lua': {
                'extensions': ['.lua'],
                'single_line': ['--'],
                'multi_line': [('--[[', ']]')],
                'string_delimiters': ['"', "'"]
            },
            'r': {
                'extensions': ['.r', '.R'],
                'single_line': ['#'],
                'multi_line': [],
                'string_delimiters': ['"', "'"]
            },
            'matlab': {
                'extensions': ['.m'],
                'single_line': ['%'],
                'multi_line': [('%{', '%}')],
                'string_delimiters': ['"', "'"]
            }
        }

    def detect_language(self, file_path: str) -> Optional[str]:

        extension = Path(file_path).suffix.lower()

        for lang, config in self.language_patterns.items():
            if extension in config['extensions']:
                return lang

        return None

    def is_in_string(self, content: str, position: int, string_delimiters: List[str]) -> bool:


        in_string = False
        string_char = None
        escaped = False

        for i, char in enumerate(content[:position]):
            if escaped:
                escaped = False
                continue

            if char == '\\':
                escaped = True
                continue

            if not in_string:
                for delimiter in string_delimiters:
                    if content[i:].startswith(delimiter):
                        in_string = True
                        string_char = delimiter
                        break
            else:
                if content[i:].startswith(string_char):
                    in_string = False
                    string_char = None

        return in_string

    def remove_single_line_comments(self, content: str, comment_markers: List[str], 
                                  string_delimiters: List[str]) -> str:

        lines = content.split('\n')
        cleaned_lines = []

        for line in lines:
            cleaned_line = line

            for marker in comment_markers:
                marker_pos = line.find(marker)
                while marker_pos != -1:

                    if not self.is_in_string(line, marker_pos, string_delimiters):

                        cleaned_line = line[:marker_pos].rstrip()
                        break
                    else:

                        marker_pos = line.find(marker, marker_pos + 1)

                if marker_pos != -1:
                    break

            cleaned_lines.append(cleaned_line)

        return '\n'.join(cleaned_lines)

    def remove_multi_line_comments(self, content: str, comment_pairs: List[Tuple[str, str]], 
                                 string_delimiters: List[str]) -> str:

        for start_marker, end_marker in comment_pairs:
            while True:
                start_pos = content.find(start_marker)
                if start_pos == -1:
                    break


                if self.is_in_string(content, start_pos, string_delimiters):

                    temp_content = content[:start_pos] + ' ' * len(start_marker) + content[start_pos + len(start_marker):]
                    content = temp_content
                    continue

                end_pos = content.find(end_marker, start_pos + len(start_marker))
                if end_pos == -1:

                    content = content[:start_pos]
                    break


                before_comment = content[:start_pos]
                after_comment = content[end_pos + len(end_marker):]

                content = before_comment + after_comment

        return content

    def clean_excessive_whitespace(self, content: str) -> str:

        lines = content.split('\n')
        cleaned_lines = []

        i = 0
        while i < len(lines):
            line = lines[i]


            if line.strip():
                cleaned_lines.append(line)
                i += 1
            else:

                empty_start = i
                while i < len(lines) and not lines[i].strip():
                    i += 1


                empty_count = i - empty_start


                if len(cleaned_lines) == 0 or i >= len(lines):

                    if empty_count > 0:
                        cleaned_lines.append('')
                else:

                    lines_to_keep = min(empty_count, 2)
                    for _ in range(lines_to_keep):
                        cleaned_lines.append('')


        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()


        while cleaned_lines and not cleaned_lines[0].strip():
            cleaned_lines.pop(0)

        return '\n'.join(cleaned_lines)

    def remove_comments(self, file_path: str) -> Tuple[str, bool]:

        language = self.detect_language(file_path)

        if not language:
            return f"Unsupported file type: {file_path}", False

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
        except Exception as e:
            return f"Error reading file {file_path}: {str(e)}", False

        config = self.language_patterns[language]


        if config['single_line']:
            content = self.remove_single_line_comments(
                content, config['single_line'], config['string_delimiters']
            )


        if config['multi_line']:
            content = self.remove_multi_line_comments(
                content, config['multi_line'], config['string_delimiters']
            )


        content = self.clean_excessive_whitespace(content)

        return content, True

    def process_file(self, input_path: str, output_path: str = None, backup: bool = True, 
                     preserve_whitespace: bool = False) -> bool:

        cleaned_content, success = self.remove_comments(input_path)

        if not success:
            print(f"Failed to process {input_path}: {cleaned_content}")
            return False


        if not preserve_whitespace:
            cleaned_content = self.clean_excessive_whitespace(cleaned_content)


        if output_path is None:
            output_path = input_path


        if backup and output_path == input_path:
            backup_path = f"{input_path}.bak"
            try:
                with open(input_path, 'r', encoding='utf-8') as original:
                    with open(backup_path, 'w', encoding='utf-8') as backup_file:
                        backup_file.write(original.read())
                print(f"Backup created: {backup_path}")
            except Exception as e:
                print(f"Warning: Could not create backup for {input_path}: {str(e)}")


        try:
            with open(output_path, 'w', encoding='utf-8') as output_file:
                output_file.write(cleaned_content)
            print(f"Comments removed from: {input_path}")
            if output_path != input_path:
                print(f"Output written to: {output_path}")
            return True
        except Exception as e:
            print(f"Error writing to {output_path}: {str(e)}")
            return False

    def process_directory(self, directory: str, recursive: bool = True, 
                         output_dir: str = None, backup: bool = True,
                         preserve_whitespace: bool = False) -> int:

        processed_count = 0
        directory_path = Path(directory)

        if not directory_path.is_dir():
            print(f"Error: {directory} is not a directory")
            return 0


        supported_extensions = set()
        for config in self.language_patterns.values():
            supported_extensions.update(config['extensions'])


        pattern = "**/*" if recursive else "*"
        files_to_process = []

        for file_path in directory_path.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                files_to_process.append(file_path)


        for file_path in files_to_process:
            relative_path = file_path.relative_to(directory_path)

            if output_dir:
                output_path = Path(output_dir) / relative_path
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path = str(output_path)
            else:
                output_path = str(file_path)

            if self.process_file(str(file_path), output_path, backup, preserve_whitespace):
                processed_count += 1

        return processed_count

def main():
    parser = argparse.ArgumentParser(
        description="Remove comments from various scripting language files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Supported Languages:
  Python, JavaScript, TypeScript, Java, C/C++, Shell scripts, Perl, Ruby,
  PHP, CSS/SCSS/Sass, HTML/XML, SQL, Lua, R, MATLAB

Examples:
  python comment_remover.py script.py
  python comment_remover.py script.js -o clean_script.js
  python comment_remover.py ./src -r --no-backup
  python comment_remover.py ./project -o ./clean_project -r
        """
    )

    parser.add_argument('input', help='Input file or directory')
    parser.add_argument('-o', '--output', help='Output file or directory')
    parser.add_argument('-r', '--recursive', action='store_true',
                       help='Process directories recursively')
    parser.add_argument('--no-backup', action='store_true',
                       help='Do not create backup files')
    parser.add_argument('--preserve-whitespace', action='store_true',
                       help='Do not clean up excessive whitespace left by removed comments')

    args = parser.parse_args()

    remover = CommentRemover()

    if os.path.isfile(args.input):

        success = remover.process_file(args.input, args.output, not args.no_backup, 
                                     args.preserve_whitespace)
        if success:
            print("File processed successfully!")
        else:
            print("Failed to process file.")
            return 1

    elif os.path.isdir(args.input):

        processed = remover.process_directory(
            args.input, args.recursive, args.output, not args.no_backup,
            args.preserve_whitespace
        )
        print(f"\nProcessed {processed} files successfully!")

    else:
        print(f"Error: {args.input} is not a valid file or directory")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())