package meta.example.supermarket.people

import meta.classLifting.SpecialInstructions
import squid.quasi.lift
import scala.util.Random

/* Auto generated from genCustomers */

@lift
class Customer70 extends People with BiWeekly with MealPlan14 with BargainShopper {
  def main(): Unit = {
    while(true) {
      SpecialInstructions.handleMessages()
      customerInfo

      buyListedItems(shoppingList.targetItems, (Random.nextFloat < priceConscious))
      buyRandItems(shoppingList.randItems)

      List.range(0, frequency).foreach(_ => {
        consumeFood(mealPlan)
        consumeFood
        customerInfo
        SpecialInstructions.waitTurns(1)
      })
    }
  }
}
