import React from 'react';
import { useParams } from 'react-router-dom';

const RentalDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  return <div><h1>Rental Detail - ID: {id}</h1><p>Under construction</p></div>;
};

export default RentalDetail;