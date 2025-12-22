import React from 'react';
import { Link } from 'react-router-dom';

const HomePage = () => {
  return (
    <div>
      <h2>Home Page</h2>
      <p>Welcome to the lab management app!</p>
      <Link to="/about">Go to About Page</Link>
    </div>
  );
};

export default HomePage;
