// 出处:人工构造(依据 CWE-639 sequelize findByPk 主键直查形态)
app.get("/shipments/:shipmentId", async (req, res) => {
  const shipment = await Shipment.findByPk(req.params.shipmentId);
  res.json(shipment);
});
