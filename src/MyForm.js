import React from 'react';
import { Formik, Field, Form, ErrorMessage } from 'formik';
import * as Yup from 'yup';
import { Button, TextField } from '@mui/material';

// 表单验证 Schema
const validationSchema = Yup.object({
  name: Yup.string().required('Required'),
  email: Yup.string().email('Invalid email address').required('Required')
});

const MyForm = () => (
  <div style={{ width: '300px', margin: '0 auto', padding: '20px' }}>
    <h2>Form with Validation</h2>
    <Formik
      initialValues={{ name: '', email: '' }}
      validationSchema={validationSchema}
      onSubmit={(values) => alert(JSON.stringify(values, null, 2))}
    >
      <Form>
        <div>
          <Field
            name="name"
            as={TextField}
            label="Your Name"
            variant="outlined"
            fullWidth
            margin="normal"
          />
          <ErrorMessage name="name" component="div" />
        </div>
        <div>
          <Field
            name="email"
            as={TextField}
            label="Your Email"
            variant="outlined"
            fullWidth
            margin="normal"
          />
          <ErrorMessage name="email" component="div" />
        </div>
        <div style={{ marginTop: '10px' }}>
          <Button type="submit" variant="contained" color="primary">
            Submit
          </Button>
        </div>
      </Form>
    </Formik>
  </div>
);

export default MyForm;
