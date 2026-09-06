<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/TERUZvxght/TERUZvxght/main/assets/header-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/TERUZvxght/TERUZvxght/main/assets/header-light.svg">
  <img alt="TERUZ — Developer tools, games, and systems" src="https://raw.githubusercontent.com/TERUZvxght/TERUZvxght/main/assets/header-light.svg" width="100%">
</picture>

**開発ツールをつくり、ゲームやシステムの仕組みを探る。**

Ruby / Rails の開発体験を改善する **[OvalLSP](https://github.com/TERUZvxght/OvalLSP)** を開発しています。個人開発を通じて、ゲームづくりや制作を支えるツール、低レイヤーの実験にも取り組んでいます。

[OvalLSP 公式サイト](https://teruzvxght.github.io/OvalLSP/ja/) · [VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=teruz.ovallsp) · [English summary](#english-summary)

## 公開プロジェクト

### [OvalLSP](https://github.com/TERUZvxght/OvalLSP)

**Ruby / Rails 向けの言語サーバーと VS Code 拡張。**

Ruby のコードを静的に解析し、信頼済みワークスペースでは Rails アプリの実行時情報も組み合わせて、エディタの補完・型情報・コード移動を支援します。

- **コードを読む・たどる** — ホバーでの型情報、定義への移動、参照検索。
- **Rails の文脈を扱う** — Active Record のカラム・関連、ルートヘルパーなどを補完に反映。
- **言語サーバーから拡張機能まで** — Ruby 製 Core Server、TypeScript 製 VS Code クライアント、Rails Runtime Agent を開発。

`Ruby` `TypeScript` `Prism` `RBS / RBI` `Language Server Protocol`

**Preview 公開中。配布対象は macOS / Apple Silicon。** 対応環境と機能の検証範囲は [サポート表](https://github.com/TERUZvxght/OvalLSP/blob/main/docs/SUPPORT_MATRIX.md)、今後の予定は [ロードマップ](https://github.com/TERUZvxght/OvalLSP/blob/main/docs/ROADMAP.md) にまとめています。

[日本語 README](https://github.com/TERUZvxght/OvalLSP/blob/main/README.ja.md) · [ソースコード](https://github.com/TERUZvxght/OvalLSP) · [インストール案内](https://teruzvxght.github.io/OvalLSP/ja/getting-started.html)

<sub>開発に集中するため、現在は外部からの Issue 提案・Pull Request を受け付けていません。最新の受付状況はリポジトリの README をご確認ください。</sub>

## 取り組んでいる分野

公開作品のほかにも、次の分野で開発・試作を重ねています。

| 分野 | 取り組み | 使用技術 |
| :--- | :--- | :--- |
| **開発ツール** | 言語サーバー、エディタ拡張、開発支援 | Ruby / TypeScript / LSP |
| **ゲームと制作基盤** | ゲーム、通信・データ管理のライブラリ、制作支援ツール | C# / Unity / Python / Blender |
| **AI の活用と実験** | ローカル AI、エージェント、制作ワークフローの自動化 | Python / Rust / Ollama |
| **システムの仕組み** | OS・カーネル、言語モデルの実験的な実装 | Rust |
| **アプリとユーティリティ** | デスクトップ・モバイルアプリ、Bot | TypeScript / Swift / Dart / Go |

## 開発で大切にしていること

- **使う場面から考える。** エディタやゲーム、制作の流れの中で、何ができるようになるかを起点にする。
- **仕組みまで掘り下げる。** アプリだけでなく、それを支える解析・通信・データ管理にも取り組む。
- **確かめたことを伝える。** 動作確認できた範囲と制約を、コード・テスト・ドキュメントに残す。

## English summary

I'm **TERUZ**, an independent developer building developer tools and exploring games and systems.

My public project is **[OvalLSP](https://github.com/TERUZvxght/OvalLSP)**, a Ruby / Rails language server and VS Code extension combining static analysis with runtime information from trusted Rails workspaces. It is available as a **Preview for macOS on Apple Silicon**. External issue proposals and pull requests are currently paused; see the repository README for the current policy.

My other development and experiments span game tooling, local AI workflows, systems programming, and desktop and mobile apps.

[Project website](https://teruzvxght.github.io/OvalLSP/) · [VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=teruz.ovallsp)
