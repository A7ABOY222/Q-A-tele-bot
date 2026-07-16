import { Router, type IRouter } from "express";
import healthRouter from "./health";
import { authRouter } from "./auth";
import { guildsRouter } from "./guilds";

const router: IRouter = Router();

router.use(healthRouter);
router.use("/auth", authRouter);
router.use("/guilds", guildsRouter);

export default router;
