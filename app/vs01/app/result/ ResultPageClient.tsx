'use client';

import { useEffect, useState } from 'react';

type LatestJson = {
  filename: string;
  data: Array<{ model: string; price: number }>;
  updatedAt: string;
} | null;

interface Props {
  secretHref: string;
  latestJson: LatestJson;
}

export default function ResultPageClient({ secretHref, latestJson }: Props) {
  const [displayContent, setDisplayContent] = useState<string>(
    'データがまだありません。\n1ページ目で「JSON出力」ボタンを押した後、このページを開いてください。'
  );
  const [isDataAvailable, setIsDataAvailable] = useState(false);
  const [copyStatus, setCopyStatus] = useState('📋 クリップボードにコピー');

  useEffect(() => {
    if (!latestJson || !latestJson.data) {
      setDisplayContent(
        'データがまだありません。\n\n直近30分以内に change_bo フォルダ内に作成された _end.json が見つかりませんでした。'
      );
      setIsDataAvailable(false);
      return;
    }

    const { filename, data, updatedAt } = latestJson;
    const itemCount = data.length;

    let content = `【ファイル名】 ${filename}\n`;
    content += `【更新日時】 ${updatedAt}\n`;
    content += `【変換件数】 ${itemCount} 件\n`;
    content += `══════════════════════════════════════\n\n`;

    content += itemCount === 0 
      ? 'データがありません。' 
      : JSON.stringify(data, null, 2);

    setDisplayContent(content);
    setIsDataAvailable(true);
  }, [latestJson]);

  const handleCopy = () => {
    if (!latestJson?.data) {
      alert('コピーするデータがありません。');
      return;
    }

    navigator.clipboard
      .writeText(JSON.stringify(latestJson.data, null, 2))
      .then(() => {
        setCopyStatus('✅ コピーしました！');
        setTimeout(() => setCopyStatus('📋 クリップボードにコピー'), 2000);
      })
      .catch(() => alert('コピーに失敗しました'));
  };

  const handleBack = () => {
    window.location.href = secretHref;
  };

  return (
    <div className="wrapper">
      <header>
        <a href={secretHref} className="back-link">← トップに戻る</a>
        <h1>実行結果</h1>
        <a href={secretHref} className="hidden-star">＊</a>
      </header>

      <div className="result-container" id="result-display">
        {displayContent}
      </div>

      <div className="actions">
        <button className="back-btn" onClick={handleBack}>
          トップに戻る
        </button>
        <button className="copy-btn" onClick={handleCopy} disabled={!isDataAvailable}>
          {copyStatus}
        </button>
      </div>

      <div className="status">
        harakiriizm Result Viewer • 直近30分以内に作成された _end.json を自動表示します
        {isDataAvailable && latestJson && (
          <div style={{ marginTop: '8px', color: '#2ecc71', fontWeight: 500 }}>
            ● {latestJson.filename} を表示中
          </div>
        )}
      </div>
    </div>
  );
}