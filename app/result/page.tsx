import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import ResultPageClient from './ResultPageClient';

const getSecretHref = () => {
  const __dirname = dirname(fileURLToPath(import.meta.url));
  const appFolderPassPath = join(__dirname, '../app-folder-pass.txt');
  const baseAppPath = readFileSync(appFolderPassPath, 'utf8').trim();
  if (!baseAppPath) {
    throw new Error('app-folder-pass.txt is empty. パスを設定してください。');
  }
  return `${baseAppPath.replace(/\/$/, '')}/secret/harakiriim-03`;
};

export default function ResultPage() {
  const secretHref = getSecretHref();
  return <ResultPageClient secretHref={secretHref} />;
}
