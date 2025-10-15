# TTCDX Vendor RAG Frontend

TTCDX Vendor RAG の検索フロントエンドアプリケーションです。

## 技術スタック

- **Framework**: Next.js 14 (Pages Router)
- **Styling**: Tailwind CSS + shadcn/ui
- **State Management**: React Query (@tanstack/react-query)
- **Language**: TypeScript
- **Hosting**: AWS Amplify

## 機能

- 自然言語でのベンダー検索
- 検索結果の表示（スコア、メタデータ）
- 検索パラメータの調整（結果数、MMR、類似度計算方法）
- URL同期（検索状態の永続化）
- レスポンシブデザイン
- アクセシビリティ対応

## 開発

### セットアップ

```bash
cd frontend
npm install
```

### 環境変数

`.env.local` ファイルを作成し、以下を設定：

```
NEXT_PUBLIC_API_BASE=https://api.3ii.biz
```

### 開発サーバー起動

```bash
npm run dev
```

### ビルド

```bash
npm run build
npm start
```

## デプロイ

AWS Amplify でのデプロイに対応しています。

### 必要な設定

1. `amplify.yml` でビルド設定を定義
2. 環境変数 `NEXT_PUBLIC_API_BASE` を設定
3. CORS設定でAmplifyドメインを許可

## API仕様

### エンドポイント

- `POST ${NEXT_PUBLIC_API_BASE}/search`

### リクエスト

```typescript
type SearchRequest = {
  query: string;
  k?: number;              // default 5
  use_mmr?: boolean;       // default false
  similarity_method?: 'distance' | string; // default 'distance'
}
```

### レスポンス

```typescript
type SearchResult = {
  text: string;
  score: number;
  metadata: {
    vendor_id: string;
    [k: string]: any;
  };
};
type SearchResponse = { results: SearchResult[] };
```

## ディレクトリ構造

```
frontend/
├── src/
│   ├── pages/              # Next.js Pages Router
│   │   ├── index.tsx
│   │   └── _app.tsx
│   ├── styles/             # グローバルスタイル
│   │   └── globals.css
│   ├── components/          # React コンポーネント
│   │   ├── ui/             # shadcn/ui コンポーネント
│   │   ├── SearchBar.tsx
│   │   ├── Controls.tsx
│   │   ├── ResultCard.tsx
│   │   └── ...
│   └── lib/                # ユーティリティ
│       ├── api.ts
│       ├── time.ts
│       └── utils.ts
├── public/
├── package.json
├── next.config.js
├── tailwind.config.js
└── amplify.yml
```
