import React from 'react';
import { Link } from 'react-router-dom';

const Navbar = () => {
  return (
    <nav className="navbar navbar-expand-lg navbar-light bg-light">
      <div className="container-fluid">
        <Link className="navbar-brand" to="/">
          Lab Management App
        </Link>
        <div className="navbar-nav">
          <Link className="nav-link" to="/register">
            Register
          </Link>
          <Link className="nav-link" to="/records">
            Records
          </Link>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
