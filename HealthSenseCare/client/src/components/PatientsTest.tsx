import { useEffect, useState } from "react";
import { getPatients } from "../lib/api";

export default function PatientsTest() {
  const [patients, setPatients] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    getPatients()
      .then(setPatients)
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div>
      <h2>Patients Test</h2>
      {error && <div style={{ color: "red" }}>{error}</div>}
      <ul>
        {patients.map((p: any) => (
          <li key={p.id}>{p.name}</li>
        ))}
      </ul>
    </div>
  );
}
