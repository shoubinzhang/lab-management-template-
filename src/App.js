import React from 'react';
import { Route, Routes } from 'react-router-dom'; // 这里不再使用 <Router>
import Home from './Home';
import About from './About';
import MyForm from './MyForm';

const App = () => {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/about" element={<About />} />
      <Route path="/form" element={<MyForm />} />
    </Routes>
  );
};

export default App;
