import React from 'react';
import { useParams } from 'react-router-dom';

const VehicleDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  
  return (
    <div>
      <h1>Vehicle Detail - ID: {id}</h1>
      <p>Vehicle detail page is under construction.</p>
    </div>
  );
};

export default VehicleDetail;