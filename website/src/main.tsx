import "@fontsource/anton/latin-400.css";
import "@fontsource/work-sans/latin-400.css";
import "@fontsource/work-sans/latin-400-italic.css";
import "@fontsource/work-sans/latin-500.css";
import "@fontsource/work-sans/latin-600.css";
import "@fontsource/work-sans/latin-700.css";
import "@fontsource/dm-mono/latin-400.css";
import "@fontsource/dm-mono/latin-500.css";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
// Self-hosted fonts (Latin subsets only): no third-party font requests.
import "./index.css";
import App from "./App";

createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
