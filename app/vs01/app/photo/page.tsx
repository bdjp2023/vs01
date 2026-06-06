// File: app/secret/harakiriim-03/page.tsx
'use client';

import { useEffect, useRef, useState, useCallback, ChangeEvent, DragEvent } from 'react';

/* ===== 型定義 ===== */
type ImageItem = {
  type: 'image';
  name: string;
  data: string; // dataURL (JPEG)
};

type FolderItem = {
  type: 'folder';
  name: string;
  children: Array<FolderItem | ImageItem>;
};

type AnyItem = FolderItem | ImageItem;

const STORAGE_KEY = 'harakiriVault';
const MAX_IMAGE_WIDTH = 1280;
const JPEG_QUALITY = 0.82;

/* ===== ユーティリティ ===== */
function createRoot(): FolderItem {
  return { type: 'folder', name: '/', children: [] };
}

function cloneTree(node: FolderItem): FolderItem {
  return JSON.parse(JSON.stringify(node));
}

function getFolderByPath(root: FolderItem, path: string[]): FolderItem | null {
  let cur: FolderItem = root;
  for (const seg of path) {
    const next = cur.children.find(
      (c) => c.type === 'folder' && c.name === seg
    ) as FolderItem | undefined;
    if (!next) return null;
    cur = next;
  }
  return cur;
}

async function fileToCompressedJpegDataUrl(file: File): Promise<string> {
  const dataUrl = await new Promise<string>((resolve, reject) => {
    const fr = new FileReader();
    fr.onload = () => resolve(fr.result as string);
    fr.onerror = reject;
    fr.readAsDataURL(file);
  });

  const img = await new Promise<HTMLImageElement>((resolve, reject) => {
    const im = new Image();
    im.onload = () => resolve(im);
    im.onerror = reject;
    im.src = dataUrl;
  });

  const scale = Math.min(1, MAX_IMAGE_WIDTH / img.width);
  const w = Math.round(img.width * scale);
  const h = Math.round(img.height * scale);

  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d');
  if (!ctx) return dataUrl;
  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, w, h);
  ctx.drawImage(img, 0, 0, w, h);
  return canvas.toDataURL('image/jpeg', JPEG_QUALITY);
}

export default function SecretVaultPage() {
  const [root, setRoot] = useState<FolderItem>(() => createRoot());
  const [path, setPath] = useState<string[]>([]);
  const [newFolderName, setNewFolderName] = useState('');
  const [previewSrc, setPreviewSrc] = useState<string | null>(null);
  const [toast, setToast] = useState<string>('');
  const [toastShow, setToastShow] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const toastTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  /* ===== 初期ロード ===== */
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved) as FolderItem;
        if (parsed && parsed.type === 'folder') {
          setRoot(parsed);
        }
      }
    } catch {
      // ignore
    }
  }, []);

  /* ===== 保存 ===== */
  const persist = useCallback((next: FolderItem) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    } catch {
      showToast('保存に失敗しました（容量制限の可能性）');
    }
  }, []);

  /* ===== トースト ===== */
  const showToast = (msg: string) => {
    setToast(msg);
    setToastShow(true);
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    toastTimerRef.current = setTimeout(() => setToastShow(false), 2200);
  };

  /* ===== 現在フォルダ ===== */
  const currentFolder = getFolderByPath(root, path) ?? root;

  /* ===== 操作: フォルダ移動 ===== */
  const enterFolder = (name: string) => {
    setPath((p) => [...p, name]);
  };
  const goUp = () => {
    setPath((p) => p.slice(0, -1));
  };
  const jumpToIndex = (index: number) => {
    setPath((p) => p.slice(0, index));
  };

  /* ===== 操作: 新規フォルダ ===== */
  const createFolder = () => {
    const name = newFolderName.trim();
    if (!name) {
      showToast('フォルダ名を入力してください');
      return;
    }
    if (currentFolder.children.some((c) => c.name === name)) {
      showToast('同名の項目が既に存在します');
      return;
    }
    const next = cloneTree(root);
    const target = getFolderByPath(next, path);
    if (!target) return;
    target.children.push({ type: 'folder', name, children: [] });
    setRoot(next);
    persist(next);
    setNewFolderName('');
    showToast(`フォルダ「${name}」を作成しました`);
  };

  /* ===== 操作: アップロード ===== */
  const handleFiles = async (files: FileList | File[]) => {
    const list = Array.from(files).filter((f) => f.type.startsWith('image/'));
    if (list.length === 0) {
      showToast('画像ファイルを選択してください');
      return;
    }
    const next = cloneTree(root);
    const target = getFolderByPath(next, path);
    if (!target) return;

    let added = 0;
    for (const f of list) {
      try {
        const dataUrl = await fileToCompressedJpegDataUrl(f);
        let name = f.name.replace(/\.[^.]+$/, '') + '.jpg';
        let dup = 1;
        const base = name.replace(/\.jpg$/, '');
        while (target.children.some((c) => c.name === name)) {
          name = `${base}_${dup}.jpg`;
          dup++;
        }
        target.children.push({ type: 'image', name, data: dataUrl });
        added++;
      } catch {
        // skip
      }
    }
    setRoot(next);
    persist(next);
    showToast(`${added}件アップロードしました`);
  };

  const onFileInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(e.target.files);
      e.target.value = '';
    }
  };

  const onDrop = (e: DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files) handleFiles(e.dataTransfer.files);
  };

  /* ===== 操作: 削除 ===== */
  const deleteItem = (name: string) => {
    if (!confirm(`「${name}」を削除しますか？`)) return;
    const next = cloneTree(root);
    const target = getFolderByPath(next, path);
    if (!target) return;
    target.children = target.children.filter((c) => c.name !== name);
    setRoot(next);
    persist(next);
    showToast('削除しました');
  };

  const clearCurrentFolder = () => {
    if (!confirm('このフォルダを空にしますか？（中身がすべて削除されます）')) return;
    const next = cloneTree(root);
    const target = getFolderByPath(next, path);
    if (!target) return;
    target.children = [];
    setRoot(next);
    persist(next);
    showToast('フォルダを空にしました');
  };

  /* ===== ツリー描画用 ===== */
  type FlatNode = { name: string; path: string[]; depth: number };
  const flatTree: FlatNode[] = [];
  const walk = (node: FolderItem, p: string[], depth: number) => {
    flatTree.push({ name: node.name, path: p, depth });
    node.children.forEach((c) => {
      if (c.type === 'folder') walk(c, [...p, c.name], depth + 1);
    });
  };
  walk(root, [], 0);

  const isActive = (p: string[]) =>
    p.length === path.length && p.every((s, i) => s === path[i]);

  /* ===== レンダリング ===== */
  return (
    <>
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
      <link
        href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap"
        rel="stylesheet"
      />
      <style>{`
        :root {
          --bg: #fff;
          --primary: #4a90e2;
          --gray: #f5f7fa;
          --text: #333;
          --border: #ddd;
          --radius: 8px;
          --shadow: 0 2px 6px rgba(0,0,0,0.08);
          --danger: #e24a4a;
          --folder: #f5c451;
          --image: #7ac57a;
        }
        * { box-sizing: border-box; }
        body {
          font-family: 'Noto Sans JP', sans-serif;
          font-weight: 400;
          background: var(--gray);
          color: var(--text);
          margin: 0;
          padding: 0;
          min-height: 100vh;
        }
        header {
          background: var(--bg);
          box-shadow: var(--shadow);
          padding: 16px 24px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          position: sticky;
          top: 0;
          z-index: 10;
        }
        header .back-link {
          color: var(--primary);
          text-decoration: none;
          font-weight: 500;
          font-size: 0.95rem;
        }
        header .back-link:hover { text-decoration: underline; }
        header h1 {
          margin: 0;
          font-size: 1.25rem;
          font-weight: 700;
          text-align: center;
          flex: 1;
        }
        header .hidden-star {
          color: var(--bg);
          text-decoration: none;
          user-select: none;
          font-size: 0.95rem;
          width: 80px;
          text-align: right;
        }
        .breadcrumb-bar {
          background: var(--bg);
          border-bottom: 1px solid var(--border);
          padding: 12px 24px;
          display: flex;
          align-items: center;
          gap: 12px;
          flex-wrap: wrap;
        }
        .breadcrumb-bar .current-label { font-size: 0.8rem; color: #888; }
        .breadcrumb-bar .current-folder {
          font-weight: 700; font-size: 1rem; color: var(--primary);
        }
        .breadcrumb-path {
          display: flex; align-items: center; gap: 4px;
          flex-wrap: wrap; font-size: 0.9rem;
        }
        .breadcrumb-path a {
          color: var(--primary); text-decoration: none; cursor: pointer;
        }
        .breadcrumb-path a:hover { text-decoration: underline; }
        .breadcrumb-path .sep { color: #aaa; }
        .vault-container {
          display: grid;
          grid-template-columns: 220px 1fr 280px;
          gap: 16px;
          max-width: 1300px;
          margin: 16px auto;
          padding: 0 16px;
        }
        .vault-panel {
          background: var(--bg);
          border-radius: var(--radius);
          box-shadow: var(--shadow);
          padding: 16px;
        }
        .vault-panel h2 {
          margin: 0 0 12px;
          font-size: 0.95rem;
          font-weight: 700;
          color: var(--primary);
          border-bottom: 2px solid var(--gray);
          padding-bottom: 6px;
        }
        .folder-tree {
          list-style: none; margin: 0; padding: 0;
          font-size: 0.9rem; max-height: 60vh; overflow-y: auto;
        }
        .folder-tree li {
          padding: 6px 8px; border-radius: 4px; cursor: pointer;
          user-select: none; white-space: nowrap; overflow: hidden;
          text-overflow: ellipsis;
        }
        .folder-tree li:hover { background: var(--gray); }
        .folder-tree li.active { background: var(--primary); color: #fff; }
        .folder-tree .tree-icon { margin-right: 6px; }
        .content-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
          gap: 12px;
          min-height: 300px;
        }
        .item-card {
          display: flex; flex-direction: column; align-items: center;
          padding: 12px 6px;
          border: 1px solid var(--border);
          border-radius: var(--radius);
          cursor: pointer;
          transition: transform 0.15s, box-shadow 0.15s, background 0.15s;
          text-decoration: none; color: var(--text);
          background: var(--bg); position: relative;
        }
        .item-card:hover {
          transform: translateY(-2px);
          box-shadow: var(--shadow);
          background: var(--gray);
        }
        .item-card .item-mark {
          font-size: 2.4rem; line-height: 1; margin-bottom: 8px;
        }
        .item-card.folder .item-mark { color: var(--folder); }
        .item-card.image  .item-mark { color: var(--image); }
        .item-card.up     .item-mark { color: #888; }
        .item-card .item-name {
          font-size: 0.8rem; text-align: center;
          word-break: break-all; line-height: 1.3;
          max-height: 2.6em; overflow: hidden;
        }
        .item-card .item-thumb {
          width: 100%; height: 70px; object-fit: cover;
          border-radius: 4px; margin-bottom: 6px;
        }
        .item-card .item-delete {
          position: absolute; top: 4px; right: 4px;
          background: var(--danger); color: #fff;
          border: none; border-radius: 50%;
          width: 20px; height: 20px;
          font-size: 0.75rem; line-height: 1;
          cursor: pointer; opacity: 0;
          transition: opacity 0.15s;
        }
        .item-card:hover .item-delete { opacity: 1; }
        .empty-folder {
          grid-column: 1 / -1; text-align: center;
          color: #aaa; padding: 40px 0; font-size: 0.9rem;
        }
        .upload-zone {
          border: 2px dashed var(--border);
          border-radius: var(--radius);
          padding: 24px 12px; text-align: center;
          cursor: pointer;
          transition: border-color 0.2s, background 0.2s;
          margin-bottom: 12px;
          display: block;
        }
        .upload-zone:hover,
        .upload-zone.dragover {
          border-color: var(--primary);
          background: var(--gray);
        }
        .upload-zone .up-icon {
          font-size: 2rem; color: var(--primary); margin-bottom: 6px;
        }
        .upload-zone p {
          margin: 4px 0; font-size: 0.85rem; color: #666;
        }
        .upload-zone input[type=file] { display: none; }
        .new-folder-row {
          display: flex; gap: 6px; margin-bottom: 12px;
        }
        .new-folder-row input {
          flex: 1; padding: 6px 10px;
          border: 1px solid var(--border);
          border-radius: var(--radius);
          font-family: inherit; font-size: 0.85rem;
        }
        .btn {
          border: none; border-radius: var(--radius);
          padding: 7px 12px; font-family: inherit;
          font-size: 0.85rem; font-weight: 500;
          cursor: pointer; transition: opacity 0.2s;
        }
        .btn:hover { opacity: 0.85; }
        .btn-primary { background: var(--primary); color: #fff; }
        .btn-danger  { background: var(--danger);  color: #fff; }
        .btn-gray    { background: var(--gray); color: var(--text); border: 1px solid var(--border); }
        .btn-block   { width: 100%; }
        .upload-info {
          font-size: 0.75rem; color: #888;
          margin-top: 8px; line-height: 1.5;
        }
        .preview-modal {
          display: none; position: fixed; inset: 0;
          background: rgba(0,0,0,0.75); z-index: 100;
          align-items: center; justify-content: center; padding: 20px;
        }
        .preview-modal.show { display: flex; }
        .preview-modal img {
          max-width: 90vw; max-height: 85vh;
          border-radius: var(--radius);
          box-shadow: 0 4px 24px rgba(0,0,0,0.4);
        }
        .preview-modal .close-btn {
          position: absolute; top: 16px; right: 24px;
          background: var(--bg); border: none;
          border-radius: 50%; width: 36px; height: 36px;
          font-size: 1.2rem; cursor: pointer;
        }
        .toast {
          position: fixed; bottom: 24px; left: 50%;
          transform: translateX(-50%) translateY(100px);
          background: var(--text); color: #fff;
          padding: 10px 20px; border-radius: var(--radius);
          box-shadow: var(--shadow);
          opacity: 0; transition: all 0.3s;
          z-index: 200; font-size: 0.9rem;
        }
        .toast.show {
          opacity: 1; transform: translateX(-50%) translateY(0);
        }
        @media (max-width: 900px) {
          .vault-container { grid-template-columns: 1fr; }
        }
        @media (max-width: 600px) {
          header { padding: 12px 16px; }
          header h1 { font-size: 1.05rem; }
          header .back-link { font-size: 0.85rem; }
          .breadcrumb-bar { padding: 10px 16px; }
          .content-grid { grid-template-columns: repeat(auto-fill, minmax(90px, 1fr)); }
          .item-card .item-mark { font-size: 2rem; }
        }
        @media (max-width: 480px) {
          header h1 { font-size: 0.95rem; }
          .content-grid { grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); }
          .item-card { padding: 8px 4px; }
          .item-card .item-name { font-size: 0.72rem; }
          .vault-panel { padding: 12px; }
        }
      `}</style>

      <header>
        <a className="back-link" href="https://harakiriizm-01.vercel.app/">
          ← トップに戻る
        </a>
        <h1>秘密のフォルダ</h1>
        <a className="hidden-star" href="https://harakiriizm-01.vercel.app/result.html">
          ＊
        </a>
      </header>

      <div className="breadcrumb-bar">
        <div>
          <div className="current-label">現在のフォルダ</div>
          <div className="current-folder" id="current-folder-name">
            {path.length === 0 ? '/' : '/' + path.join('/')}
          </div>
        </div>
        <div className="breadcrumb-path" id="breadcrumb-path">
          <a onClick={() => jumpToIndex(0)}>root</a>
          {path.map((seg, i) => (
            <span key={i} style={{ display: 'inline-flex', gap: 4 }}>
              <span className="sep">/</span>
              <a onClick={() => jumpToIndex(i + 1)}>{seg}</a>
            </span>
          ))}
        </div>
      </div>

      <main className="vault-container">
        {/* 左：フォルダツリー */}
        <aside className="vault-panel">
          <h2>📂 フォルダツリー</h2>
          <ul className="folder-tree" id="folder-tree">
            {flatTree.map((n, i) => (
              <li
                key={i}
                className={isActive(n.path) ? 'active' : ''}
                style={{ paddingLeft: 8 + n.depth * 14 }}
                onClick={() => setPath(n.path)}
                title={n.name}
              >
                <span className="tree-icon">📁</span>
                {n.depth === 0 ? 'root' : n.name}
              </li>
            ))}
          </ul>
        </aside>

        {/* 中央：内部構造 */}
        <section className="vault-panel">
          <h2 id="content-title">📁 内部構造</h2>
          <div className="content-grid" id="content-grid">
            {path.length > 0 && (
              <a className="item-card up" onClick={goUp}>
                <div className="item-mark">↩</div>
                <div className="item-name">..</div>
              </a>
            )}

            {currentFolder.children.length === 0 && path.length === 0 ? (
              <div className="empty-folder">
                このフォルダは空です。右側からアップロード／フォルダ作成ができます。
              </div>
            ) : null}

            {currentFolder.children.map((item, i) =>
              item.type === 'folder' ? (
                <a
                  key={i}
                  className="item-card folder"
                  onClick={() => enterFolder(item.name)}
                >
                  <button
                    className="item-delete"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteItem(item.name);
                    }}
                  >
                    ×
                  </button>
                  <div className="item-mark">📁</div>
                  <div className="item-name">{item.name}</div>
                </a>
              ) : (
                <a
                  key={i}
                  className="item-card image"
                  onClick={() => setPreviewSrc(item.data)}
                >
                  <button
                    className="item-delete"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteItem(item.name);
                    }}
                  >
                    ×
                  </button>
                  <img className="item-thumb" src={item.data} alt={item.name} />
                  <div className="item-name">{item.name}</div>
                </a>
              )
            )}

            {currentFolder.children.length === 0 && path.length > 0 && (
              <div className="empty-folder">このフォルダは空です。</div>
            )}
          </div>
        </section>

        {/* 右：アップロード＆操作 */}
        <aside className="vault-panel">
          <h2>⬆ アップロード</h2>

          <label
            className={`upload-zone${dragOver ? ' dragover' : ''}`}
            id="upload-zone"
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
          >
            <div className="up-icon">📤</div>
            <p>
              <strong>クリックまたはドロップ</strong>
            </p>
            <p style={{ fontSize: '0.75rem' }}>画像ファイルをここへ</p>
            <input
              type="file"
              id="file-input"
              accept="image/*"
              multiple
              ref={fileInputRef}
              onChange={onFileInputChange}
            />
          </label>

          <div className="new-folder-row">
            <input
              type="text"
              id="new-folder-input"
              placeholder="新規フォルダ名"
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') createFolder();
              }}
            />
            <button
              className="btn btn-primary"
              id="btn-create-folder"
              onClick={createFolder}
            >
              作成
            </button>
          </div>

          <button
            className="btn btn-gray btn-block"
            id="btn-go-up"
            style={{ marginBottom: 8 }}
            onClick={goUp}
            disabled={path.length === 0}
          >
            ↑ 上の階層へ
          </button>
          <button
            className="btn btn-danger btn-block"
            id="btn-clear-folder"
            onClick={clearCurrentFolder}
          >
            このフォルダを空にする
          </button>

          <div className="upload-info">
            ※ 画像は JPEG 形式で localStorage に保存されます。
            <br />
            容量制限（約 5MB 前後）を超えるとエラーになります。
          </div>
        </aside>
      </main>

      {/* プレビューモーダル */}
      <div
        className={`preview-modal${previewSrc ? ' show' : ''}`}
        onClick={() => setPreviewSrc(null)}
      >
        <button className="close-btn" onClick={() => setPreviewSrc(null)}>
          ×
        </button>
        {previewSrc && <img src={previewSrc} alt="preview" />}
      </div>

      {/* トースト */}
      <div className={`toast${toastShow ? ' show' : ''}`}>{toast}</div>
    </>
  );
}