import { Route, Routes } from "react-router-dom";
import Home from "@/features/busca/Home";
import Layout from "@/shared/Layout";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
      </Route>
    </Routes>
  );
}
