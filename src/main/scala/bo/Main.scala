package bo

import java.io.{FileDescriptor, FileOutputStream, PrintStream}

import Securities.{Flour, Land}
import Simulation.SimLib.{Buyer, Mill}
import Simulation.{Person, Simulation}
import _root_.Simulation.SimLib.{Farm, Source}

object Main {
  val metrics: Seq[Int] => Seq[Double] = xs => {
    val s = new Simulation
    initializeSimulation(s)
    s.sims.zip(xs).foreach(t => t._1.capital = t._2)
    callSimulation(s, 1000)
    List(s.sims.map(_.capital.toDouble / 100 / s.sims.size).sum)
  }

  val bounds: Seq[(Int, Int)] = for(_ <- 1 to numberOfSims) yield (0, 100)

  def main(args: Array[String]): Unit = {
    args(0) match {
      case "generate" =>
        BOUtil.generateXYPairs("target/scala-2.11/xypairs", bounds, metrics, 1)

      case "evaluate" =>
        val file = scala.io.Source.fromFile("target/scala-2.11/xypairs")
        val lines = file.getLines().toList
        val Xs = lines.filter(_.startsWith("x:")).map(_.substring(2).split(' ').map(_.toInt))
        val Ys = lines.filter(_.startsWith("y:")).map(_.substring(2).split(' ').map(_.toDouble))
        println(BOUtil.error(Xs, Ys, metrics))
    }
  }

  def numberOfSims = 16

  def initializeSimulation(s: Simulation, mute: Boolean = true): Unit = {
    if (mute)
      Console.setOut(new PrintStream(new FileOutputStream("target/scala-2.11/initLog")))

    GLOBAL.silent = true
    val f = new Farm(s)
    val m = new Mill(s)
    //val c   = new Cinema(s);
    //val rf  = new CattleFarm(s);
    //val mcd = new McDonalds(s);
    val landlord = new Source(Land, 20, 100000 * 100, s)
    //val freudensprung = new Source(Beef,   100,  26000*100, s);
    //val silo          = new Source(Wheat, 1000,   6668*100, s);
    //val silo2         = new Trader(Whear, 100, s);
    //val billa         = new Trader(Flour, 50, s);
    val mehlbuyer = Buyer(Flour, () => 40, s)

    val people = for (x <- 1 to 12) yield new Person(s, false)

    s.init(List(
      landlord,
      //silo,
      // silo2, billa, freudensprung,
      f, m,
      // c, rf, mcd,
      mehlbuyer
    ) ++ people.toList)

    Console.out.flush()
    Console.setOut(new PrintStream(new FileOutputStream(FileDescriptor.out)))
  }

  def callSimulation(s: Simulation, iterations: Int, mute: Boolean = true): Unit = {
    if (mute)
      Console.setOut(new PrintStream(new FileOutputStream("target/scala-2.11/runLog")))

    s.run(iterations)

    Console.out.flush()
    Console.setOut(new PrintStream(new FileOutputStream(FileDescriptor.out)))
  }
}