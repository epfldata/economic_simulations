package meta.example.supermarket.people

import meta.classLifting.SpecialInstructions
import squid.quasi.lift
import scala.util.Random

@lift
class Customer2 extends People with BiWeekly with MealPlan1 with TargetShopper {

  def main(): Unit = {
    while(true) {
      SpecialInstructions.handleMessages()
      customerInfo

      buyListedItems(shoppingList.targetItems, Random.nextFloat<priceConscious)
      if (!needBased) buyRandItems(shoppingList.randItems)

      List.range(0, frequency).foreach(_ => {
        consumeFood(mealPlan)
        consumeFood
        customerInfo
        SpecialInstructions.waitTurns(1)
      })
    }
  }
}
