import csv
import itertools
import sys

PROBS = {

    # Unconditional probabilities for having gene
    "gene": {
        2: 0.01,
        1: 0.03,
        0: 0.96
    },

    "trait": {

        # Probability of trait given two copies of gene
        2: {
            True: 0.65,
            False: 0.35
        },

        # Probability of trait given one copy of gene
        1: {
            True: 0.56,
            False: 0.44
        },

        # Probability of trait given no gene
        0: {
            True: 0.01,
            False: 0.99
        }
    },

    # Mutation probability
    "mutation": 0.01
}


def main():
    # Check for proper usage
    if len(sys.argv) != 2:
        sys.exit("Usage: python heredity.py data.csv")
    people = load_data(sys.argv[1])

    # Keep track of gene and trait probabilities for each person
    probabilities = {
        person: {
            "gene": {
                2: 0,
                1: 0,
                0: 0
            },
            "trait": {
                True: 0,
                False: 0
            }
        }
        for person in people
    }

    # Loop over all sets of people who might have the trait
    names = set(people)
    for have_trait in powerset(names):

        # Check if current set of people violates known information
        fails_evidence = any(
            (people[person]["trait"] is not None and
             people[person]["trait"] != (person in have_trait))
            for person in names
        )
        if fails_evidence:
            continue

        # Loop over all sets of people who might have the gene
        for one_gene in powerset(names):
            for two_genes in powerset(names - one_gene):
                # Update probabilities with new joint probability
                p = joint_probability(people, one_gene, two_genes, have_trait)
                update(probabilities, one_gene, two_genes, have_trait, p)

    # Ensure probabilities sum to 1
    normalize(probabilities)

    # Print results
    for person in people:
        print(f"{person}:")
        for field in probabilities[person]:
            print(f"  {field.capitalize()}:")
            for value in probabilities[person][field]:
                p = probabilities[person][field][value]
                print(f"    {value}: {p:.4f}")


def load_data(filename):
    """
    Load gene and trait data from a file into a dictionary.
    File assumed to be a CSV containing fields name, mother, father, trait.
    mother, father must both be blank, or both be valid names in the CSV.
    trait should be 0 or 1 if trait is known, blank otherwise.
    """
    data = dict()
    with open(filename) as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"]
            data[name] = {
                "name": name,
                "mother": row["mother"] or None,
                "father": row["father"] or None,
                "trait": (True if row["trait"] == "1" else
                          False if row["trait"] == "0" else None)
            }
    return data


def powerset(s):
    """
    Return a list of all possible subsets of set s.
    """
    s = list(s)
    return [
        set(s) for s in itertools.chain.from_iterable(
            itertools.combinations(s, r) for r in range(len(s) + 1)
        )
    ]


def joint_probability(people, one_gene, two_genes, have_trait):
    """
    Compute and return a joint probability.

    The probability returned should be the probability that
        * everyone in set `one_gene` has one copy of the gene, and
        * everyone in set `two_genes` has two copies of the gene, and
        * everyone not in `one_gene` or `two_gene` does not have the gene, and
        * everyone in set `have_trait` has the trait, and
        * everyone not in set` have_trait` does not have the trait.
    """
    joint_p = 1
    # zero_genes = set(people.keys()) - two_genes - one_gene
    for person in people:

        # Calculate probability to have the genes of interest
        this_genes = get_nbr_genes(person, one_gene, two_genes)
        if people[person]['mother'] is None:  # Assumes both parents info, or nothing
            gene_prob = PROBS['gene'][this_genes]
        else:  # If there is parent's info
            prob_mother = get_parent_prob(people[person]['mother'], one_gene, two_genes)
            prob_father = get_parent_prob(people[person]['father'], one_gene, two_genes)

            if this_genes == 0:
                gene_prob = (1 - prob_mother) * (1 - prob_father)  # None can transmit
            elif this_genes == 1:
                gene_prob = (1 - prob_mother) * prob_father + prob_mother * (1 - prob_father)  # Two possibilities
            else:
                gene_prob = prob_father * prob_mother  # Both need to transmit

        # Calculate probability to have trait, given genes of interest
        trait = get_trait(person, have_trait)  # Trait for this person
        trait_prob = PROBS['trait'][this_genes][trait]

        joint_p *= gene_prob * trait_prob  # Accumulates joint probability of all people

    return joint_p


def get_trait(person, have_trait):
    return True if person in have_trait else False


def get_nbr_genes(person, one_gene, two_genes):
    """
    Return number of genes for person
    """
    return (2 if person in two_genes
                 else 1 if person in one_gene
                        else 0)


def get_parent_prob(parent, one_gene, two_genes):
    """
    Return probability that parent transmits the gene
    """
    nbr_genes = get_nbr_genes(parent, one_gene, two_genes)  # Number of genes for parent

    return (0.01 if nbr_genes == 0
            else 0.5 if nbr_genes == 1
                     else 0.99)


def update(probabilities, one_gene, two_genes, have_trait, p):
    """
    Add to `probabilities` a new joint probability `p`.
    Each person should have their "gene" and "trait" distributions updated.
    Which value for each distribution is updated depends on whether
    the person is in `have_gene` and `have_trait`, respectively.
    """
    for person in probabilities:
        nbr_genes = get_nbr_genes(person, one_gene, two_genes)
        probabilities[person]['gene'][nbr_genes] += p

        trait = get_trait(person, have_trait)
        probabilities[person]['trait'][trait] += p


def normalize(probabilities):
    """
    Update `probabilities` such that each probability distribution
    is normalized (i.e., sums to 1, with relative proportions the same).
    """
    for person, dists in probabilities.items():
        for dist, values in dists.items():
            this_sum = sum(values.values())
            for value in values:
                probabilities[person][dist][value] /= this_sum


if __name__ == "__main__":
    main()
