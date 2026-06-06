// File: app/result/page.tsx
import { readFileSync, readdirSync, statSync } from 'node:fs';
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

// 直下の change_bo フォルダから直近30分以内に作成されたJSONを探す
const getLatestChangeBoJson = () => {
  try {
    const changeBoDir = join(process.cwd(), 'change_bo'); // ← ここを直下のchange_boフォルダに指定

    const files = readdirSync(changeBoDir).filter(file => 
      file.endsWith('_end.json')  // MM_dd_end.json のみを対象
    );

    if (files.length === 0) return null;

    const now = Date.now();
    const THIRTY_MINUTES = 30 * 60 * 1000; // 30分

    let latestFile: string | null = null;
    let latestTime = 0;

    for (const file of files) {
      const filePath = join(changeBoDir, file);
      const stats = statSync(filePath);
      
      // 更新時刻で判定（作成時刻が欲しい場合は birthtimeMs に変更可）
      const fileTime = stats.mtimeMs;

      if (now - fileTime < THIRTY_MINUTES && fileTime > latestTime) {
        latestTime = fileTime;
        latestFile = file;
      }
    }

    if (!latestFile) return null;

    const filePath = join(changeBoDir, latestFile);
    const content = readFileSync(filePath, 'utf8');
    const jsonData = JSON.parse(content);

    return {
      filename: latestFile,
      data: jsonData,
      updatedAt: new Date(latestTime).toLocaleString('ja-JP')
    };
  } catch (error) {
    console.error('change_boフォルダの読み込みに失敗しました:', error);
    return null;
  }
};

export default function ResultPage() {
  const secretHref = getSecretHref();
  const latestJson = getLatestChangeBoJson();

  return (
    <ResultPageClient 
      secretHref={secretHref} 
      latestJson={latestJson}        // ← 新しく追加
    />
  );
}