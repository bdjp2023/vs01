// File: app/page.tsx
'use client';

import { useEffect, useRef, useState, ChangeEvent } from 'react';

const STORAGE_KEY = 'harakiriData';
const RESULT_KEY = 'harakiriResult'; // Python側が完了時に書き込むキー
const INITIAL_SU_COUNT = 6; // 初期表示は3列×2行 = 6セル

type Phase = 'idle' | 'running' | 'done';

type FormData = {
  hp: string;
  jump: string;
  back: string;
  // su1, su2, ... が動的に増える
  [key: string]: string;
};

function pad2(n: number) {
  return n.toString().padStart(2, '0');
}

function formatTime(sec: number) {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${pad2(m)}:${pad2(s)}`;
}

export default function HomePage() {
  /* ===== 状態 ===== */
  const [suCount, setSuCount] = useState<number>(INITIAL_SU_COUNT);
  const [form, setForm] = useState<FormData>(() => {
    const init: FormData = { hp: '', jump: '', back: '' };
    for (let i = 1; i <= INITIAL_SU_COUNT; i++) init[`su${i}`] = '';
    return init;
  });
  const [phase, setPhase] = useState<Phase>('idle');
  const [elapsed, setElapsed] = useState<number>(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  /* ===== 入力変更 ===== */
  const onChange = (key: string) => (e: ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [key]: e.target.value }));
  };

  /* ===== セル追加（3つずつ） ===== */
  const addRow = () => {
    setSuCount((prev) => {
      const next = prev + 3;
      setForm((f) => {
        const updated = { ...f };
        for (let i = prev + 1; i <= next; i++) updated[`su${i}`] = '';
        return updated;
      });
      return next;
    });
  };

  /* ===== クリア（フォーム＋localStorage＋セル数＋タイマー＋phase 全リセット） ===== */
  const onClear = () => {
    // タイマー停止
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = null;
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = null;

    // localStorage 全クリア（関連キー）
    try {
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem(RESULT_KEY);
    } catch {
      // ignore
    }

    // 状態リセット
    setSuCount(INITIAL_SU_COUNT);
    const init: FormData = { hp: '', jump: '', back: '' };
    for (let i = 1; i <= INITIAL_SU_COUNT; i++) init[`su${i}`] = '';
    setForm(init);
    setPhase('idle');
    setElapsed(0);
  };

  /* ===== スタート（localStorage 保存 + タイマー作動） ===== */
  const onStart = () => {
    // 現在のフォーム内容を配列化（要素数1のオブジェクト配列）
    const payload = [{ ...form }];
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
      localStorage.removeItem(RESULT_KEY); // 前回の結果をクリア
    } catch {
      alert('localStorage への保存に失敗しました');
      return;
    }

    setPhase('running');
    setElapsed(0);

    // タイマー作動
    timerRef.current = setInterval(() => {
      setElapsed((prev) => prev + 1);
    }, 1000);

    // Python 側の完了検知（localStorage に harakiriResult が書き込まれたら完了）
    pollRef.current = setInterval(() => {
      try {
        const result = localStorage.getItem(RESULT_KEY);
        if (result) {
          // タイマー停止
          if (timerRef.current) clearInterval(timerRef.current);
          timerRef.current = null;
          if (pollRef.current) clearInterval(pollRef.current);
          pollRef.current = null;
          setPhase('done');
        }
      } catch {
        // ignore
      }
    }, 1000);
  };

  /* ===== 「結果を見る」ボタン ===== */
  const onGoResult = () => {
    window.location.href = '/result';
  };

  /* ===== 「入力データDL」リンク ===== */
  const onDownload = () => {
    const payload = [{ ...form }];
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'inputizm.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  /* ===== クリーンアップ ===== */
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  /* ===== セル入力欄を3列×n行のグリッドで描画 ===== */
  const renderSuGrid = () => {
    const rows: React.JSX.Element[] = [];
    for (let i = 0; i < suCount; i += 3) {
      const r1 = i + 1;
      const r2 = i + 2;
      const r3 = i + 3;
      rows.push(
        <div className="su-row" key={`row-${i}`}>
          <div className="row">
            <label htmlFor={`su${r1}`}>セル{r1}</label>
            <input
              id={`su${r1}`}
              type="text"
              value={form[`su${r1}`] ?? ''}
              onChange={onChange(`su${r1}`)}
            />
          </div>
          <div className="row">
            <label htmlFor={`su${r2}`}>セル{r2}</label>
            <input
              id={`su${r2}`}
              type="text"
              value={form[`su${r2}`] ?? ''}
              onChange={onChange(`su${r2}`)}
            />
          </div>
          <div className="row">
            <label htmlFor={`su${r3}`}>セル{r3}</label>
            <input
              id={`su${r3}`}
              type="text"
              value={form[`su${r3}`] ?? ''}
              onChange={onChange(`su${r3}`)}
            />
          </div>
        </div>
      );
    }
    return rows;
  };

  return (
    <>
      <link
        href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap"
        rel="stylesheet"
      />
      <style>{`
        :root{
          --bg:#fff;
          --primary:#4a90e2;
          --gray:#f5f7fa;
          --text:#333;
          --border:#ddd;
          --radius:8px;
          --shadow:0 2px 6px rgba(0,0,0,0.08);
        }
        *{box-sizing:border-box;margin:0;padding:0;}
        body{
          font-family:'Noto Sans JP',sans-serif;
          background:var(--gray);
          color:var(--text);
          display:flex;
          justify-content:center;
          padding:1rem;
        }
        .wrapper{
          background:var(--bg);
          max-width:600px;
          width:100%;
          padding:2rem;
          border-radius:var(--radius);
          box-shadow:var(--shadow);
        }
        h1{
          text-align:center;
          margin-bottom:1.5rem;
          color:var(--primary);
          font-weight:700;
        }
        .field{
          display:flex;
          align-items:center;
          margin-bottom:1rem;
        }
        .field label{
          flex:0 0 70px;
          font-weight:500;
        }
        .field input{
          flex:1;
          padding:.5rem;
          border:1px solid var(--border);
          border-radius:var(--radius);
          font-size:1rem;
          transition:border-color .2s;
        }
        .field input:focus{border-color:var(--primary);outline:none;}
        .grid{
          display:grid;
          grid-template-columns:1fr 1fr;
          gap:1rem;
        }
        .grid .row{
          display:flex;
          align-items:center;
        }
        .grid .row label{
          flex:0 0 45px;
          font-size:.9rem;
          white-space:nowrap;
        }
        .grid .row input{
          flex:1;
          padding:.4rem;
          border:1px solid var(--border);
          border-radius:var(--radius);
          font-size:.9rem;
        }
        /* セル用の3列グリッド */
        .su-row{
          display:grid;
          grid-template-columns:1fr 1fr 1fr;
          gap:.6rem;
          margin-bottom:.6rem;
        }
        .su-row .row label{
          flex:0 0 50px;
          font-size:.85rem;
          white-space:nowrap;
        }
        .su-row .row input{
          flex:1;
          padding:.4rem;
          border:1px solid var(--border);
          border-radius:var(--radius);
          font-size:.85rem;
        }
        .add-btn{
          width:100%;
          padding:.5rem;
          margin-top:.5rem;
          background:var(--primary);
          color:#fff;
          border:none;
          border-radius:var(--radius);
          cursor:pointer;
          font-weight:500;
        }
        .actions{
          display:flex;
          gap:.5rem;
          margin-top:1.5rem;
          justify-content:center;
        }
        .actions button{
          flex:1;
          padding:.6rem;
          border:none;
          border-radius:var(--radius);
          font-weight:500;
          color:#fff;
          cursor:pointer;
        }
        .actions button:disabled{
          cursor:not-allowed;
          opacity:0.85;
        }
        .clear{background:#e74c3c;}
        .start{background:#2ecc71;}
        .running{background:#f1c40f;}
        .result{background:var(--primary);}
        .timer{
          margin-top:1rem;
          text-align:center;
          font-size:1.2rem;
          font-weight:500;
        }
        .download-link{
          margin-left:.5rem;
          font-size:.9rem;
          color:var(--primary);
          cursor:pointer;
          text-decoration:underline;
        }
        @media (max-width:480px){
          .field label,.grid .row label{flex-basis:60px;}
          .grid{grid-template-columns:1fr;}
          .su-row{grid-template-columns:1fr;}
        }
      `}</style>

      <div className="wrapper">
        <h1>サンプルページ</h1>

        {/* URL 入力 + 入力データDL */}
        <div className="field">
          <label htmlFor="hp">HP</label>
          <input
            id="hp"
            type="text"
            value={form.hp}
            onChange={onChange('hp')}
          />
          <a className="download-link" onClick={onDownload}>
            入力データDL
          </a>
        </div>

        {/* ジャンプ + バック（2カラム） */}
        <div className="grid" style={{ marginBottom: '1rem' }}>
          <div className="row">
            <label htmlFor="jump">ジャンプ</label>
            <input
              id="jump"
              type="text"
              value={form.jump}
              onChange={onChange('jump')}
            />
          </div>
          <div className="row">
            <label htmlFor="back">バック</label>
            <input
              id="back"
              type="text"
              value={form.back}
              onChange={onChange('back')}
            />
          </div>
        </div>

        {/* セル入力欄（3列×n行） */}
        {renderSuGrid()}

        {/* 追加ボタン */}
        <button className="add-btn" onClick={addRow}>
          ＋ 行を追加
        </button>

        {/* タイマー */}
        <div className="timer">{formatTime(elapsed)}</div>

        {/* アクションボタン */}
        <div className="actions">
          <button className="clear" onClick={onClear}>
            クリア
          </button>
          {phase === 'idle' && (
            <button className="start" onClick={onStart}>
              スタート
            </button>
          )}
          {phase === 'running' && (
            <button className="running" disabled>
              実行中…
            </button>
          )}
          {phase === 'done' && (
            <button className="result" onClick={onGoResult}>
              結果を見る
            </button>
          )}
        </div>
      </div>
    </>
  );
}