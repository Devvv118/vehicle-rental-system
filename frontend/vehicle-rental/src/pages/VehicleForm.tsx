import React from 'react';
import { useParams } from 'react-router-dom';

const VehicleForm: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const isEdit = Boolean(id);
  
  return (
    <div>
      <h1>{isEdit ? 'Edit Vehicle' : 'Add Vehicle'}</h1>
      <p>Vehicle form is under construction.</p>
    </div>
  );
};

export default VehicleForm;