import React from "react";
import { Provider } from "react-redux";
import { BrowserRouter } from "react-router-dom";
import store from "./redux/store";
import LogInteraction from "./pages/LogInteraction";
import "./styles.css";

export default function App() {
  return (
    <Provider store={store}>
      <BrowserRouter>
        <LogInteraction />
      </BrowserRouter>
    </Provider>
  );
}